python /home/ubuntu/transformers/examples/language-modeling/run_clm.py \
    --model_name_or_path gpt2 \
    --dataset_name wikitext \
    --dataset_config_name wikitext-2-raw-v1 \
    --do_train \
    --do_eval \
    --output_dir ./new_models

aws s3 cp --recursive ./new_models s3://transformers-bucket/Models/
