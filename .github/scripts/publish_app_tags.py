import importlib
import inspect
import os
import pkgutil
from typing import Callable, Tuple

from git import Repo, Remote

import puma.apps

APP_MODULE = 'puma.apps'


def find_app_classes() -> list[type]:
    """
    Finds the classes of all supported apps: the classes in puma.apps with a supported version (see
    @supported_version). New apps are found automatically.
    :return: The app classes, sorted by module.
    """
    app_classes = []
    for module_info in pkgutil.walk_packages(puma.apps.__path__, f'{APP_MODULE}.'):
        module = importlib.import_module(module_info.name)
        for _, cls in inspect.getmembers(module, inspect.isclass):
            # only classes defined in this module, with their own supported version (not inherited)
            if cls.__module__ == module.__name__ and 'supported_version' in vars(cls):
                app_classes.append(cls)
    return sorted(app_classes, key=lambda cls: cls.__module__)


def get_app_name_and_platform(app_action_class: Callable) -> Tuple:
    """
    Extract the app name and platform from the module of the app action class. The module structure is as follows:
        puma.apps.android.whatsapp.whatsapp
        puma.apps.ios.messages.messages
    Note that this may not work anymore when the module structure is altered.
    :param app_action_class: App action class
    :return: app name, platform
    """
    app_path = app_action_class.__module__
    platform = app_path.split(".")[2]
    app_name = app_path.split(".")[3]
    return platform, app_name


def remove_app_tag(local_repo: Repo, remote_repo: Remote, tag_name: str):
    """
    Remove the tag from the remote repo and all its dependencies. Assumes the tag actually is present.
    :param local_repo: Local repository
    :param remote_repo: Remote repository
    :param tag_name: Tag name
    """
    try:
        local_repo.delete_tag(tag_name)
        print(f"Tag '{tag_name}' has been removed from the local repository.")
    except Exception as e:
        print(f"Failed to delete the tag: {e}")

    try:
        remote_repo.push(refspec=f':refs/tags/{tag_name}')
        print(f"Tag '{tag_name}' has been removed from the remote repository.")
    except Exception as e:
        print(f"Failed to delete the tag from the remote repository: {e}")


if __name__ == '__main__':
    repo_dir = os.getenv('GITHUB_WORKSPACE', os.getcwd())
    token = os.getenv('GITHUB_TOKEN')

    puma_repo = Repo(repo_dir)

    origin = puma_repo.remote()
    remote_url = origin.url.replace('https://', f'https://{token}@')
    origin.set_url(remote_url)

    repo_tags = puma_repo.tags
    for app_action_class in find_app_classes():
        platform, app_name = get_app_name_and_platform(app_action_class)
        app_version_tag = f"{app_name}-{platform}-v{app_action_class.supported_version}"# Note that supported_version is a custom decorator, so your IDE might not autocomplete it.
        if app_version_tag in repo_tags:
            remove_app_tag(puma_repo, origin, app_version_tag)
        try:
            puma_repo.create_tag(app_version_tag)
            origin.push(app_version_tag)
            print(f"Successfully created tag {app_version_tag}.")
        except Exception as e:
            print(f"Something went wrong when creating or pushing the tag {app_version_tag}.")
