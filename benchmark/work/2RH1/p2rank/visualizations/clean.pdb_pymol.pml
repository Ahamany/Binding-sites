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
select surf_pocket1, protein and id [3098,667,3293,1299,3099,3133,635,638,1301,633,637,1292,1294,1295,1296,1297,1303,1304,1314,1288,1309,1311,1308,688,694,3072,3109,3110,659,662,666,1356,1359,3165,1317,1319,1183,1380,1383,1379,1358,1350,1352,1404,1405,1378,3291,3255,3256,3257,3259,3260,3261,3227,3230,3231,3210,3127,3129,3130,3131,3132,3156,3158,3153,3151,3152,3189,3197,3188,3190,687,713,686,689,690,1403,1410,459,629,630,478,480,481,1281,1289,1290,3329,3331,657,658,660,3264,3269,3301,3303,487,3268,3270,3233,3234,483,485,475] 
set surface_color,  pcol1, surf_pocket1 
set_color pcol2 = [0.302,0.278,0.702]
select surf_pocket2, protein and id [3433,271,3434,3447,3449,286,285,287,256,265,3430,2953,2954,2956,2957,2964,2918,2925,788,873,2980,2955,299,301,308,2986,2988,2978,2979,3456,3458,309,3407,2987,300,786] 
set surface_color,  pcol2, surf_pocket2 
set_color pcol3 = [0.631,0.361,0.902]
select surf_pocket3, protein and id [1233,1124,1160,1231,1234,1097,1150,602,605,1158,637,1286,1287,1293,1298,1236,1238,636,638,562,563,564,566,597,1280,1283,1275,1227] 
set surface_color,  pcol3, surf_pocket3 
set_color pcol4 = [0.678,0.278,0.702]
select surf_pocket4, protein and id [3528,183,3379,3380,3417,3494,3492,3489,3391,158,153,155,3381] 
set surface_color,  pcol4, surf_pocket4 
set_color pcol5 = [0.902,0.361,0.682]
select surf_pocket5, protein and id [2889,1570,2886,1573,1574,2887,2888,1538,1568,1569,2898,2899,2882,2885,2890,2939,2900,1539,1541] 
set surface_color,  pcol5, surf_pocket5 
set_color pcol6 = [0.702,0.278,0.341]
select surf_pocket6, protein and id [400,681,399,650,652,1017,675,1075] 
set surface_color,  pcol6, surf_pocket6 
set_color pcol7 = [0.902,0.522,0.361]
select surf_pocket7, protein and id [489,3269,3301,3275,3277,3299,3300,3305,3339,79,110,60,33,88,488] 
set surface_color,  pcol7, surf_pocket7 
set_color pcol8 = [0.702,0.596,0.278]
select surf_pocket8, protein and id [1479,1473,1475,1480,3018,3017,3013,3011,1544,2990,2992,1542,1502,1503,1506,1477,1501,1511] 
set surface_color,  pcol8, surf_pocket8 
   

deselect

orient
