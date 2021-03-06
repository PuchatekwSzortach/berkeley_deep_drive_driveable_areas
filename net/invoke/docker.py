"""
Module with docker commands
"""

import invoke


@invoke.task
def build_app_container(context):
    """
    Build app container

    :param context: invoke.Context instance
    """

    command = (
        "DOCKER_BUILDKIT=1 docker build "
        "--tag puchatek_w_szortach/berkeley_deep_drive_driveable_areas:latest "
        "-f ./docker/app.Dockerfile ."
    )

    context.run(command, echo=True)


@invoke.task
def run(context, config_path):
    """
    Run app container

    Args:
        context (invoke.Context): invoke context instance
        config_path (str): path to configuration file
    """

    import os

    import net.utilities

    config = net.utilities.read_yaml(config_path)

    # Define run options that need a bit of computations
    run_options = {
        # Use gpu runtime if host has cuda installed
        "gpu_capabilities": "--gpus all" if "/cuda/" in os.environ["PATH"] else "",
        # A bit of sourcery to create data volume that can be shared with docker-compose containers
        "log_data_volume": os.path.basename(os.path.abspath('.') + '_log_data'),
        "network_name": os.path.basename(os.path.abspath(os.path.curdir)) + "_default",
        "data_directory_on_host": os.path.abspath(config["data_directory_on_host"]),
        "models_directory_on_host": os.path.abspath(config["models_directory_on_host"]),
    }

    command = (
        "docker run -it --rm "
        # Attach container to same network as docker-compose set up for backend services
        "--net {network_name} "
        "{gpu_capabilities} "
        "-v $PWD:/app:delegated "
        "-v {log_data_volume}:/tmp "
        "-v {data_directory_on_host}:/data "
        "-v {models_directory_on_host}:/models "
        # We don't expose .git directory to app container,
        # but mlflow client tries to acess it, so tell to be quiet when it fails
        "--env GIT_PYTHON_REFRESH=quiet "
        "puchatek_w_szortach/berkeley_deep_drive_driveable_areas:latest /bin/bash"
    ).format(**run_options)

    context.run(command, pty=True, echo=True)
