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
select surf_pocket1, protein and id [69,71,75,77,78,80,81,90,91,85,1001,98,99,93,1000,999,100,55,61,62,67,68,72,89,65,52,106,929,930,927,931,1005,911,88,656,657,658,222,623,625,626,627,629,240,631,654,655,421,230,231,39,45,50,646,466,467,691,425,256,690,227,228,983,208,239,241,266,1193,950,386,1212,1287,1288,1289,1290,408,422,426,428,384,385,381,1534,899,900,901,1545,1057,1558,1564,1055,1584,1585,108,897,896,1019,1021,1018,1044,1045,1047,1049,1317,1318,1321,1361,1323,1362,1285,1283,415] 
set surface_color,  pcol1, surf_pocket1 
set_color pcol2 = [0.365,0.278,0.702]
select surf_pocket2, protein and id [1953,1803,1804,1921,1954,2696,2338,2339,2340,2644,2663,2904,2906,2925,2712,2717,2718,2642,2714,2713,2731,2734,2757,2758,2760,2768,2608,2609,1807,1812,1813,2770,3277,3272,1821,1944,1935,1943,1978,1979,2099,2694,2662,1774,1775,1778,1779,1780,2998,1781,2999,3002,3001,3000,3036,1794,1768,1802,1801,1782,1784,1785,1790,1791,2611,2612,2613,2614,2622,1792,1788,3247,3258,3298,3034,2370,2371,2134,1969,2128,2131,2141,2180,2368,2369,2117,2098,2120,2121,2127,2342,1940,1941,2336,2344,2367] 
set surface_color,  pcol2, surf_pocket2 
set_color pcol3 = [0.792,0.361,0.902]
select surf_pocket3, protein and id [834,811,829,1515,845,850,851,1390,1367,1366,1389,1326,1337,1327,53,815,56,60,831,1335,1332] 
set surface_color,  pcol3, surf_pocket3 
set_color pcol4 = [0.702,0.278,0.533]
select surf_pocket4, protein and id [2524,3040,3101,3103,2542,2564,3050,3048,3039,1766,1769,2521,1773,2544,2547,2528,2537] 
set surface_color,  pcol4, surf_pocket4 
set_color pcol5 = [0.902,0.361,0.361]
select surf_pocket5, protein and id [951,966,1176,292,949,963,965,294,265,1190,264,1181,1204,1202,1203,262,240] 
set surface_color,  pcol5, surf_pocket5 
set_color pcol6 = [0.702,0.533,0.278]
select surf_pocket6, protein and id [1986,2007,2005,2662,2664,2676,2679,2889,2678,2694,1975,1977,1978,1974,2917,1950,1953] 
set surface_color,  pcol6, surf_pocket6 
   

deselect

orient
