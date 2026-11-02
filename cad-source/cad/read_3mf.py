"""Independent 3MF geometry reader. Uses document-path AND resource ID.
Some general mesh readers alias unnamed Bambu resources within one document;
this parser resolves component paths and preserves every material region.
"""
from pathlib import PurePosixPath
import zipfile, posixpath
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
NS='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
def matrix(s):
 m=np.eye(4)
 if s:m[:3,:]=np.array([float(x) for x in s.split()]).reshape(4,3).T
 return m

def read(path):
 scene=trimesh.Scene();docs={};counter=0
 with zipfile.ZipFile(path) as z:
  def document(name):
   name=name.lstrip('/')
   if name not in docs:docs[name]=ET.fromstring(z.read(name))
   return docs[name]
  def visit(doc,oid,transform,seen):
   nonlocal counter
   key=(doc,oid)
   if key in seen:raise ValueError('Cyclic 3MF components')
   root=document(doc);obj=root.find(f"{NS}resources/{NS}object[@id='{oid}']")
   if obj is None:raise ValueError(f'Missing {key}')
   mesh=obj.find(NS+'mesh')
   if mesh is not None:
    vertices=np.array([[float(v.get(k)) for k in ['x','y','z']] for v in mesh.find(NS+'vertices')]);faces=np.array([[int(f.get(k)) for k in ['v1','v2','v3']] for f in mesh.find(NS+'triangles')])
    m=trimesh.Trimesh(vertices=vertices,faces=faces,process=False);m.apply_transform(transform);name=f'{doc}:{oid}:{counter}';counter+=1
    scene.add_geometry(m,geom_name=name,node_name=name)
   for component in obj.findall(NS+'components/'+NS+'component'):
    target=component.get(P+'path') or component.get('path')
    nextdoc=(target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(posixpath.dirname(doc),target))) if target else doc
    visit(nextdoc,component.get('objectid'),transform@matrix(component.get('transform')),seen|{key})
  for item in document('3D/3dmodel.model').findall(NS+'build/'+NS+'item'):
   visit('3D/3dmodel.model',item.get('objectid'),matrix(item.get('transform')),set())
 return scene
