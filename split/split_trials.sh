for TRIAL in {1..500};
do 
    python ../scripts/data_split.py $TRIAL $1;
done

