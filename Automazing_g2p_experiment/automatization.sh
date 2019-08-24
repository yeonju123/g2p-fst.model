#!/bin/bash

seed="100"
data="hi"
orders="6 7 8"
smoothing_methods="kneser_ney witten_bell absolute katz presmoothed unsmoothed"


data_split () {
        python data_split_v1.py --seed $seed --input_path ${1}.tsv --train_path ${1}_train.tsv --dev_g_path ${1}_dev_g.tsv --dev_p_path ${1}_dev_p.tsv --test_g_path ${1}_g_test.tsv --test_p_path ${1}_p_test.tsv
}

for lang in $data; do
        data_split $lang
done

touch ${data}_result.txt

train_rewrite_eval () {
        #train pairngram model
        python train.py --input_path $train --order $1 --smoothing_method $2 --model_path ${1}_${2}_model.fst
        model_name="${1}_${2}_model.fst"
        #stringify the prediction
        python rewriter.py --word_path ${1}_dev_g.tsv --rule_path $model_name --token_type utf8 > predict.tsv
        # rewrite rule only provides the prediction. A code should be created for putting gold and prediction together. resulting file name is ${1}_{2}_eval.tsv
        #evaluate word/label error rate
        python evaluate.py ${1}_${2}_eval.tsv >> ${data}_result.txt #find a way to write down a log info

}



for order in $orders; do
        for smoothing_method in $smoothing_methods; do
                train_rewrite_eval $order $smoothing_method

done
done


