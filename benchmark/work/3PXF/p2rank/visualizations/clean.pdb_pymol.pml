from pymol import cmd,stored

set depth_cue, 1
set fog_start, 0.4

set_color b_col, [36,36,85]
set_color t_col, [10,10,10]
set bg_rgb_bottom, b_col
set bg_rgb_top, t_col      
set bg_gradient

set  spec_power  =  200
set  spec_refl   =  0

load "data/clean.pdb", protein
create ligands, protein and organic
select xlig, protein and organic
delete xlig

hide everything, all

color white, elem c
color bluewhite, protein
#show_as cartoon, protein
show surface, protein
#set transparency, 0.15

show sticks, ligands
set stick_color, magenta




# SAS points

load "data/clean.pdb_points.pdb.gz", points
hide nonbonded, points
show nb_spheres, points
set sphere_scale, 0.2, points
cmd.spectrum("b", "green_red", selection="points", minimum=0, maximum=0.7)


stored.list=[]
cmd.iterate("(resn STP)","stored.list.append(resi)")    # read info about residues STP
lastSTP=stored.list[-1] # get the index of the last residue
hide lines, resn STP

cmd.select("rest", "resn STP and resi 0")

for my_index in range(1,int(lastSTP)+1): cmd.select("pocket"+str(my_index), "resn STP and resi "+str(my_index))
for my_index in range(1,int(lastSTP)+1): cmd.show("spheres","pocket"+str(my_index))
for my_index in range(1,int(lastSTP)+1): cmd.set("sphere_scale","0.4","pocket"+str(my_index))
for my_index in range(1,int(lastSTP)+1): cmd.set("sphere_transparency","0.1","pocket"+str(my_index))



set_color pcol1 = [0.361,0.576,0.902]
select surf_pocket1, protein and id [654,655,671,673,553,576,550,484,464,466,468,412,439,575,592,593,594,635,469,471,292,309,308,634,326,328,379,535,668,669,536,533,1213,459,460,462,1216,436,461,458,438,440,153,154,155,1197,1217,1221,1259,1258,1185,1186,1187,1194,1201,1203,528] 
set surface_color,  pcol1, surf_pocket1 
set_color pcol2 = [0.329,0.278,0.702]
select surf_pocket2, protein and id [174,1113,120,275,172,173,535,668,669,536,292,670,134,135,122,125,127,116,1114,728,754,698,702,703,694,1097,1191,1192,1185,1186,1190,1092,1093,1094,1087,1088,1085] 
set surface_color,  pcol2, surf_pocket2 
set_color pcol3 = [0.698,0.361,0.902]
select surf_pocket3, protein and id [1493,1497,1501,1489,1495,981,983,987,979,1522,2257,2246,2252,2255,2269,956,959,2262,2266,2256,958,2211,2235] 
set surface_color,  pcol3, surf_pocket3 
set_color pcol4 = [0.702,0.278,0.639]
select surf_pocket4, protein and id [1449,1899,2212,2213,2214,1463,1446,1451,1855,1858,1871,1897,2206,1864,1889,1893,1906,2221,1869,1870,1474,1484,1488,1489] 
set surface_color,  pcol4, surf_pocket4 
set_color pcol5 = [0.902,0.361,0.545]
select surf_pocket5, protein and id [83,85,182,184,299,300,280,642,644,646,38,41,282,62,79,297,293,279] 
set surface_color,  pcol5, surf_pocket5 
set_color pcol6 = [0.702,0.353,0.278]
select surf_pocket6, protein and id [2185,2186,2187,2172,2150,2179,2173,1845,2195,2197,1793,1797,2174,2033,2148,2151,2001,2002,1846] 
set surface_color,  pcol6, surf_pocket6 
set_color pcol7 = [0.902,0.729,0.361]
select surf_pocket7, protein and id [1079,1081,1595,1343,1342,745,1086,742,743,1082,1089,744,1382,1383,1371] 
set surface_color,  pcol7, surf_pocket7 
   

deselect

orient
