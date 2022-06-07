import os
from pathlib import Path

from huggingface_hub import HfApi, create_repo, upload_file

from huggingface_hub.constants import REPO_TYPES

def upload_to_hf_hub(
    object_path,
    object_name,
    object_type='model',
    use_auth_token=True,
    exist_ok=True,
    # model_config=None,
):

    token = os.environ["HF_TOKEN"]

    if token is None:
        raise ValueError(
            "You must login to the Hugging Face hub on this computer by typing `transformers-cli login` and "
            "entering your credentials to use `use_auth_token=True`. Alternatively, you can pass your own "
            "token as the `use_auth_token` argument."
        )

    path_name = Path(object_path).name

    org = HfApi().whoami(token)['name']
    repo_id = f'{org}/{object_name}'
    repo_url = f'https://huggingface.co/{org}/{object_name}'

    create_repo(repo_id=object_name,
                repo_type=object_type,
                exist_ok=exist_ok)

    repo_url = upload_file(
                    path_or_fileobj=object_path, 
                    path_in_repo=path_name, 
                    repo_id=repo_id
                    )

    return repo_url