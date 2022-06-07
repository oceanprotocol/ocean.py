import os
from pathlib import Path

from huggingface_hub import HfApi, create_repo, upload_file

def upload_to_hf_hub(
    object_path,
    commit_message='Add model',
    use_auth_token=True,
    # model_config=None,
):

    token = os.environ["HF_TOKEN"]

    if token is None:
        raise ValueError(
            "You must login to the Hugging Face hub on this computer by typing `transformers-cli login` and "
            "entering your credentials to use `use_auth_token=True`. Alternatively, you can pass your own "
            "token as the `use_auth_token` argument."
        )

    object_name = Path(object_path).name

    org = HfApi().whoami(token)['name']
    repo_name = 'test-model5'
    repo_id = f'{org}/{repo_name}'
    repo_url = f'https://huggingface.co/{org}/{repo_name}'

    create_repo(name="test-model5")

    repo_url = upload_file(
                    path_or_fileobj=object_path, 
                    path_in_repo=object_name, 
                    repo_id=repo_id
                    )

    return repo_url