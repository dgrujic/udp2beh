module srff_wrap(q, s, r);
    output q;
    input s,r; 

    srff (q, s, r);
endmodule

primitive srff (q,s,r); 
    output q; reg q; 
    input s,r; 
     
    table   
      // s r q q'   
         1 0:?:1;   
         f 0:1:-;   
         0 r:?:0;   
         0 f:0:-;   
         1 1:?:0; 
    endtable 
endprimitive

