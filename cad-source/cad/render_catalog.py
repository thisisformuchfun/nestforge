#!/usr/bin/env python3
"""Render exact STL assemblies without a display/GPU; incremental 600 x 650 PNGs.

Run: python cad/render_catalog.py [--force] [--slug lantern-pavilion]
The CPU rasterizer uses VTK only to read meshes and split normals at hard edges.
It includes a depth buffer, supersampling, directional shadow map, diffuse lights,
and a ground plane. No generated imagery or substitute geometry is used.
Install numba/llvmlite if missing; CAD_RENDER_DEPS may point at isolated packages.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
for candidate in [os.environ.get('CAD_RENDER_DEPS', ''), str(ROOT.parent / 'cad-render-deps')]:
    if candidate and Path(candidate).is_dir():
        sys.path.insert(0, candidate)

import numpy as np
from numba import njit
from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageFilter
import vtk
from vtk.util.numpy_support import vtk_to_numpy


def unit(v):
    v = np.asarray(v, dtype=np.float64)
    return v / np.linalg.norm(v)


def basis(direction):
    toward = unit(direction)
    right = unit(np.cross([0, 0, 1], toward))
    up = unit(np.cross(toward, right))
    return np.asarray([right, up, toward])


def read_mesh(path):
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(path))
    reader.MergingOn()
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(reader.GetOutputPort())
    normals.SetFeatureAngle(38)
    normals.SplittingOn()
    normals.ConsistencyOn()
    normals.ComputePointNormalsOn()
    normals.Update()
    poly = normals.GetOutput()
    if poly.GetNumberOfPoints() == 0:
        raise ValueError(f'Empty mesh: {path}')
    points = vtk_to_numpy(poly.GetPoints().GetData()).astype(np.float64)
    faces = vtk_to_numpy(poly.GetPolys().GetData()).reshape((-1, 4))[:, 1:]
    ns = vtk_to_numpy(poly.GetPointData().GetNormals()).astype(np.float64)
    return points[faces].copy(), ns[faces].copy()


@njit(cache=True)
def raster_depth(tris, width, height):
    depth = np.full((height, width), -1e20, np.float64)
    for tri in tris:
        ax, ay, az = tri[0]
        bx, by, bz = tri[1]
        cx, cy, cz = tri[2]
        den = (by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
        if abs(den) < 1e-10:
            continue
        xmin = max(0, int(math.floor(min(ax, bx, cx))))
        xmax = min(width-1, int(math.ceil(max(ax, bx, cx))))
        ymin = max(0, int(math.floor(min(ay, by, cy))))
        ymax = min(height-1, int(math.ceil(max(ay, by, cy))))
        for y in range(ymin, ymax+1):
            for x in range(xmin, xmax+1):
                u = ((by-cy)*(x+.5-cx)+(cx-bx)*(y+.5-cy))/den
                v = ((cy-ay)*(x+.5-cx)+(ax-cx)*(y+.5-cy))/den
                w = 1-u-v
                if u >= -1e-7 and v >= -1e-7 and w >= -1e-7:
                    z = u*az+v*bz+w*cz
                    if z > depth[y,x]:
                        depth[y,x] = z
    return depth


@njit(cache=True)
def shadow_at(point, shadow, light_basis, shadow_center, shadow_scale, bias):
    p = light_basis @ point
    sx = (p[0]-shadow_center[0])*shadow_scale+shadow.shape[1]*.5
    sy = (shadow_center[1]-p[1])*shadow_scale+shadow.shape[0]*.5
    count = 0
    occluded = 0.
    for yy in range(-1, 2):
        for xx in range(-1, 2):
            x, y = int(sx)+xx, int(sy)+yy
            if 0 <= x < shadow.shape[1] and 0 <= y < shadow.shape[0]:
                count += 1
                if shadow[y,x] > p[2]+bias:
                    occluded += 1
    return 1.-occluded/max(count, 1)


@njit(cache=True)
def raster_color(projected, points, normals, colors, image, depth,
                 shadow, light_basis, shadow_center, shadow_scale, diag, view):
    key = light_basis[2]
    fill = np.array([.8, -.35, .45])
    fill /= np.sqrt(np.sum(fill*fill))
    rim = np.array([-.3, .8, 1.])
    rim /= np.sqrt(np.sum(rim*rim))
    half = key+view
    half /= np.sqrt(np.sum(half*half))
    height, width = depth.shape
    for i in range(len(projected)):
        tri = projected[i]
        ax, ay, az = tri[0]
        bx, by, bz = tri[1]
        cx, cy, cz = tri[2]
        den = (by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
        if abs(den) < 1e-10:
            continue
        xmin = max(0, int(math.floor(min(ax, bx, cx))))
        xmax = min(width-1, int(math.ceil(max(ax, bx, cx))))
        ymin = max(0, int(math.floor(min(ay, by, cy))))
        ymax = min(height-1, int(math.ceil(max(ay, by, cy))))
        for y in range(ymin, ymax+1):
            for x in range(xmin, xmax+1):
                u = ((by-cy)*(x+.5-cx)+(cx-bx)*(y+.5-cy))/den
                v = ((cy-ay)*(x+.5-cx)+(ax-cx)*(y+.5-cy))/den
                w = 1-u-v
                if u < -1e-7 or v < -1e-7 or w < -1e-7:
                    continue
                z = u*az+v*bz+w*cz
                if z <= depth[y,x]:
                    continue
                depth[y,x] = z
                normal = normals[i,0]*u+normals[i,1]*v+normals[i,2]*w
                normal /= max(1e-10, np.sqrt(np.sum(normal*normal)))
                point = points[i,0]*u+points[i,1]*v+points[i,2]*w
                vis = shadow_at(point, shadow, light_basis, shadow_center,
                                shadow_scale, diag*.0024)
                diffuse = .30+.66*max(0., np.dot(normal,key))*(.32+.68*vis)
                diffuse += .22*max(0.,np.dot(normal,fill))
                diffuse += .18*max(0.,np.dot(normal,rim))
                specular = .15*max(0.,np.dot(normal,half))**40*vis
                for c in range(3):
                    image[y,x,c] = min(1.,colors[i,c]*diffuse+specular)


@njit(cache=True)
def ground_image(width, height, camera_basis, center, scale, ground,
                 shadow, light_basis, shadow_center, shadow_scale, diag):
    image = np.empty((height,width,3),np.float64)
    depth = np.full((height,width),-1e20,np.float64)
    bg = np.array([11/255.,33/255.,30/255.])
    for y in range(height):
        for x in range(width):
            px = (x+.5-width*.5)/scale+center[0]
            py = (height*.5-y-.5)/scale+center[1]
            origin = camera_basis[0]*px+camera_basis[1]*py
            t = (ground-origin[2])/camera_basis[2,2]
            point = origin+camera_basis[2]*t
            vis = shadow_at(point,shadow,light_basis,shadow_center,shadow_scale,diag*.001)
            # A quiet seamless dark green studio, with the exact mesh's cast shadow.
            vignette = max(.70,1.-.17*((x-width*.5)/(width*.7))**2-.1*((y-height*.45)/(height*.8))**2)
            glow = .023*math.exp(-((x-width*.45)**2+(y-height*.32)**2)/(width*.8)**2)
            for c in range(3):
                image[y,x,c] = (bg[c]*vignette+glow)*(.50+.50*vis)
            depth[y,x] = t
    return image, depth


def project(tris, b, center, scale, width, height):
    p = tris @ b.T
    p[:,:,0] = (p[:,:,0]-center[0])*scale+width*.5
    p[:,:,1] = (center[1]-p[:,:,1])*scale+height*.5
    return p


def render_design(meta_path, width=600, height=650, supersample=2, show_hardware=True):
    metadata = json.loads(meta_path.read_text())
    all_points, all_normals, all_colors = [], [], []
    for part in [r for p in metadata['parts'] for r in p.get('regions',[p])]:
        points, normals = read_mesh(meta_path.parent / part['file'])
        rgb = np.asarray(ImageColor.getrgb(part['color'])[:3])/255.
        all_points.append(points)
        all_normals.append(normals)
        all_colors.append(np.broadcast_to(rgb,(len(points),3)).copy())
    if show_hardware and metadata.get('revision')=='R7' and metadata.get('camera_system'):
        from render_hardware import hardware_meshes
        for points,normals,colors in hardware_meshes(metadata,read_mesh):
            all_points.append(points);all_normals.append(normals);all_colors.append(colors)
    points = np.concatenate(all_points)
    normals = np.concatenate(all_normals)
    colors = np.concatenate(all_colors)
    lo, hi = points.min(axis=(0,1)), points.max(axis=(0,1))
    diag = float(np.linalg.norm(hi-lo))
    camera = basis(metadata.get('preview_direction',[1.3,-2.,1.20]))
    projected_points = points @ camera.T
    pmin, pmax = projected_points.min(axis=(0,1)), projected_points.max(axis=(0,1))
    center = (pmin+pmax)*.5
    w,h = width*supersample,height*supersample
    scale = min(w*.79/(pmax[0]-pmin[0]),h*.79/(pmax[1]-pmin[1]))
    # Slightly above center leaves room for a natural cast shadow below.
    center[1] -= (pmax[1]-pmin[1])*.012
    light = basis([-1.3,-1.8,3.])
    lp = points @ light.T
    lmin,lmax = lp.min(axis=(0,1)),lp.max(axis=(0,1))
    lc = (lmin+lmax)*.5
    shadow_size = 1200
    ls = shadow_size*.85/max(lmax[0]-lmin[0],lmax[1]-lmin[1])
    shadow = raster_depth(project(points,light,lc,ls,shadow_size,shadow_size),shadow_size,shadow_size)
    image,depth = ground_image(w,h,camera,center,scale,lo[2]-.3,shadow,light,lc,ls,diag)
    # A broad light source softens the floor shadow; the CAD silhouette stays exact.
    floor = Image.fromarray(np.asarray(np.clip(image*255,0,255),dtype=np.uint8))
    image = np.asarray(floor.filter(ImageFilter.GaussianBlur(6*supersample)),dtype=np.float64)/255.
    raster_color(project(points,camera,center,scale,w,h),points,normals,colors,image,depth,
                 shadow,light,lc,ls,diag,camera[2])
    pixels = np.asarray(np.clip(image*255,0,255),dtype=np.uint8)
    im = Image.fromarray(pixels).resize((width,height),Image.Resampling.LANCZOS)
    target = meta_path.parent/'preview.png'
    temp = target.with_suffix('.rendering.png')
    im.save(temp,optimize=True)
    temp.replace(target)
    print(f'RENDERED {metadata["id"]}: {len(points):,} triangles -> {target}',flush=True)
    return target


def font(size):
    for path in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']:
        if Path(path).exists():
            return ImageFont.truetype(path,size)
    return ImageFont.load_default()


def contact_sheet(exports, target):
    entries = []
    for p in sorted(exports.glob('*/design.json')):
        if (p.parent/'preview.png').exists() and json.loads(p.read_text()).get('revision') in ('R2','R5','R6','R7'):
            entries.append((json.loads(p.read_text()),p.parent/'preview.png'))
    if not entries:
        return
    order=['Backyard camera feeders','Vegas camera hotels','Castles','Originals','World architecture','Game day','Whimsical','Future habitats']
    entries.sort(key=lambda e:(order.index(e[0]['family']),e[0]['name']))
    cols = min(4,len(entries))
    tile_w,tile_h = 300,372
    sheet = Image.new('RGB',(cols*tile_w,math.ceil(len(entries)/cols)*tile_h+68),'#081b18')
    draw = ImageDraw.Draw(sheet)
    draw.text((22,16),'NESTFORGE / EXACT CAD PREVIEWS',fill='#e8e8d5',font=font(20))
    draw.text((22,43),f'{len(entries)} assemblies · actual exported STL geometry',fill='#8ea6a0',font=font(12))
    for i,(meta,path) in enumerate(entries):
        x,y=(i%cols)*tile_w,68+(i//cols)*tile_h
        thumb=Image.open(path).resize((300,325),Image.Resampling.LANCZOS)
        sheet.paste(thumb,(x,y))
        draw.text((x+16,y+329),meta['name'],fill='#e8e8d5',font=font(15))
        draw.text((x+16,y+351),f'{meta["family"]} · {len(meta["parts"])} parts',fill='#8ea6a0',font=font(11))
    sheet.save(target)
    print(f'CONTACT_SHEET {target}',flush=True)


def test_render():
    """Temporary exact sphere/cube scene exercises geometry, depth and PNG output."""
    with tempfile.TemporaryDirectory(prefix='cad-render-check-') as temp:
        d=Path(temp)
        sphere=vtk.vtkSphereSource();sphere.SetRadius(20);sphere.SetCenter(0,0,25)
        sphere.SetThetaResolution(64);sphere.SetPhiResolution(48)
        writer=vtk.vtkSTLWriter();writer.SetFileName(str(d/'sphere.stl'));writer.SetInputConnection(sphere.GetOutputPort());writer.Write()
        (d/'design.json').write_text(json.dumps({'id':'temporary-test','parts':[{'file':'sphere.stl','color':'#DCA45D'}]}))
        p=render_design(d/'design.json',width=180,height=195,supersample=1)
        im=Image.open(p)
        assert im.size==(180,195) and np.asarray(im).std()>10
    print('HEADLESS_CHECK passed; temporary thumbnail deleted',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exports',type=Path,default=ROOT/'exports')
    parser.add_argument('--slug',action='append',help='Render only this slug; repeatable')
    parser.add_argument('--force',action='store_true')
    parser.add_argument('--check',action='store_true',help='Run and delete a temporary test render')
    parser.add_argument('--contact-sheet',type=Path,default=ROOT/'cad'/'catalog-overview.png')
    parser.add_argument('--width',type=int,default=600)
    parser.add_argument('--height',type=int,default=650)
    args=parser.parse_args()
    if args.check:
        test_render()
    errors=[]
    for p in sorted(args.exports.glob('*/design.json')):
        if args.slug and p.parent.name not in args.slug:
            continue
        out=p.parent/'preview.png'
        meta=json.loads(p.read_text())
        if meta.get('revision') not in ('R2','R5','R6','R7'):
            continue
        deps=[p]+[p.parent/part['file'] for part in meta['parts']]
        if not args.force and out.exists() and out.stat().st_mtime>max(q.stat().st_mtime for q in deps):
            continue
        try:
            render_design(p,args.width,args.height)
        except Exception as exc:
            errors.append(f'{p.parent.name}: {exc}')
            print(f'ERROR {errors[-1]}',file=sys.stderr,flush=True)
    args.contact_sheet.parent.mkdir(parents=True,exist_ok=True)
    contact_sheet(args.exports,args.contact_sheet)
    if errors:
        raise SystemExit('\n'.join(errors))


if __name__=='__main__':
    main()
