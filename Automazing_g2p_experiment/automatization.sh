#!/bin/bash

seed="100"
lang="hi"
orders="6 7 8"
smoothing_methods="kneser_ney witten_bell absolute katz presmoothed unsmoothed"


data_split () {
        python g2p_specific_data_split.py --seed $seed --input_path ${1}.tsv --train_path ${1}_train.tsv --g_dev_path ${1}_g_dev.tsv --p_dev_path ${1}_p_dev.tsv --g_test_path ${1}_g_test.tsv --test_p_path ${1}_p_test.tsv
}

train_rewrite () {
        #train pairngram model
        python train.py --input_path ${lang}_train --order $1 --smoothing_method $2 --model_path ${lang}_${1}_${2}_model.fst
        model_name="${lang}_${1}_${2}_model.fst"
        }

predict_merge_eval (){
	#predict
        python rewriter.py --word_path ${lang}_g_${1}.tsv --rule_path $model_name --token_type utf8 > predict.tsv       
	python data_merge.py ${lang}_p_${1}.tsv predict.tsv eval.tsv
	#evaluate word/label error rate
        python evaluate.py eval.tsv >> ${lang}_result.txt #find a way to write down a log info
}


data_split $lang
touch ${lang}_result.txt

for order in $orders; do
        for smoothing_method in $smoothing_methods; do
                train_rewrite $order $smoothing_method
		predict_merge_eval dev
done
done



