../udp2beh.py test.v test_noprimitives.v
verilator -cc test_noprimitives.v --top-module srff_wrap --exe sim.cpp
cd obj_dir
make -f Vsrff_wrap.mk
cd ..
cp obj_dir/Vsrff_wrap sim


