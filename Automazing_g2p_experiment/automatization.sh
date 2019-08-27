#!/bin/bash


set -eou pipefail


lang="hi"
seed="100"
orders="3 4 5 6 7 8"
smoothing_methods="kneser_ney witten_bell absolute katz presmoothed unsmoothed"


data_split () {
        python g2p_specific_data_split.py --seed ${1} --input_path ${2}.tsv --train_path ${2}_train.tsv --g_dev_path ${2}_g_dev.tsv --p_dev_path ${2}_p_dev.tsv --g_test_path ${2}_g_test.tsv --p_test_path ${2}_p_test.tsv
}

train_rewrite () {
        #train pairngram model
        python train.py --input_path ${lang}_train.tsv --order $1 --smoothing_method $2 --model_path ${lang}_${1}_${2}_model.fst
        model_name="${lang}_${1}_${2}"
        }

predict_merge_eval (){
	#predict
        python rewrite.py --word_path ${lang}_g_${1}.tsv --fst_path ${model_name}_model.fst --token_type utf8 > predict.tsv       
	python data_merge.py ${lang}_p_${1}.tsv predict.tsv ${model_name}_eval.tsv
	#evaluate word/label error rate
        python evaluate.py ${model_name}_eval.tsv
}

data_split $seed $lang
touch ${lang}_result.txt

for order in $orders; do
        for smoothing_method in $smoothing_methods; do
                train_rewrite $order $smoothing_method
		predict_merge_eval dev
done
done
#write a code to delete all the unnecessary files. 

