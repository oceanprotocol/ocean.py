import os
from pathlib import Path

from huggingface_hub import (
    cached_download,
    create_repo,
    HfApi,
    hf_hub_url,
    list_repo_files,
    upload_file,
)

MODEL_EXTENSIONS = [".pth", ".bin"]


def get_model_files(file_list):
    files = []
    for extension in MODEL_EXTENSIONS:
        for fil in file_list:
            if fil.endswith(extension):
                files.append(fil)
    return files


class HuggingFaceHub:
    """HuggingFace class."""

    def __init__(self) -> None:
        token = os.environ["HF_KEY"]

        if token is None:
            raise ValueError(
                "You must login to the Hugging Face hub on this computer by typing `transformers-cli login` and "
                "entering your credentials to use `use_auth_token=True`. Alternatively, you can pass your own "
                "token as the `use_auth_token` argument."
            )

        self.user = HfApi().whoami(token)["name"]

    def upload(
        self,
        path_or_fileobj: str,
        object_name: str,
        object_type: str = "model",
        use_auth_token=True,
        exist_ok=True,
    ) -> str:

        repo_id = f"{self.user}/{object_name}"
        repo_url = f"https://huggingface.co/{self.user}/{object_name}"

        repo = create_repo(
            repo_id=object_name, repo_type=object_type, exist_ok=exist_ok
        )

        filename = {"dataset": "encrypted_dataset", "model": "encrypted_pytorch_model"}

        repo_url = upload_file(
            path_or_fileobj=path_or_fileobj,
            path_in_repo=filename[object_type],
            repo_id=repo_id,
            repo_type=object_type,
        )

        return repo_url

    def download(self, object_name: str, object_type: str = "model"):
        repo_id = f"{self.user}/{object_name}"
        repo_files = list_repo_files(repo_id, repo_type=object_type)
        if object_type == "model":
            print("repo_files")
            object_files = get_model_files(repo_files)
            print(object_files)
        assert (
            len(object_files) == 1
        ), f"Too many model files in repo ({len(object_files)} files)"

        url = hf_hub_url(repo_id, object_files[0])

        return cached_download(url)
