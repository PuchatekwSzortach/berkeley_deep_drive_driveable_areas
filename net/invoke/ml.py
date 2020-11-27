"""
Module with machine learning tasks
"""

import invoke


@invoke.task
def train(_context, config_path, load_existing_model=False):
    """
    Task to train drivable areas segmentation model

    Args:
        _context (invoke.Context): context instance
        config_path (str): path to configuration file
        load_existing_model (bool): specifies if existing model should be loaded, instead of training from scratch.
        Defaults to False
    """

    import mlflow
    import tensorflow as tf

    import net.data
    import net.ml
    import net.utilities

    config = net.utilities.read_yaml(config_path)

    mlflow.set_tracking_uri(config["mlflow_tracking_uri"])
    mlflow.set_experiment("training")

    with mlflow.start_run(run_name="simple_run"):

        mlflow.tensorflow.autolog(every_n_iter=1)

        training_samples_loader = net.data.BDDSamplesDataLoader(
            images_directory=config["training_images_directory"],
            segmentations_directory=config["training_segmentations_directory"],
            labels_path=config["training_labels_directory"]
        )

        training_data_loader = net.data.TrainingDataLoader(
            samples_data_loader=training_samples_loader,
            batch_size=config["batch_size"],
            use_training_mode=True
        )

        training_dataset = tf.data.Dataset.from_generator(
            generator=lambda: iter(training_data_loader),
            output_types=(tf.float32, tf.float32),
            output_shapes=(
                tf.TensorShape([
                    None,
                    config["training_image_dimensions"]["height"],
                    config["training_image_dimensions"]["width"],
                    3
                ]),
                tf.TensorShape([
                    None,
                    config["training_image_dimensions"]["height"],
                    config["training_image_dimensions"]["width"]
                ])
            )
        ).prefetch(32)

        validatation_samples_loader = net.data.BDDSamplesDataLoader(
            images_directory=config["validation_images_directory"],
            segmentations_directory=config["validation_segmentations_directory"],
            labels_path=config["validation_labels_directory"]
        )

        validation_data_loader = net.data.TrainingDataLoader(
            samples_data_loader=validatation_samples_loader,
            batch_size=config["batch_size"],
            use_training_mode=False
        )

        validation_dataset = tf.data.Dataset.from_generator(
            generator=lambda: iter(validation_data_loader),
            output_types=(tf.float32, tf.float32),
            output_shapes=(
                tf.TensorShape([
                    None,
                    config["training_image_dimensions"]["height"],
                    config["training_image_dimensions"]["width"],
                    3
                ]),
                tf.TensorShape([
                    None,
                    config["training_image_dimensions"]["height"],
                    config["training_image_dimensions"]["width"]
                ])
            )
        ).prefetch(32)

        model = tf.keras.models.load_model(
            filepath=config["current_model_directory"],
            custom_objects={
                "get_temperature_scaled_sparse_softmax": net.ml.get_temperature_scaled_sparse_softmax}
        ) if load_existing_model else \
            net.ml.DeepLabV3PlusBuilder().get_model(categories_count=len(config["categories"]))

        print(training_dataset)
        print(validation_dataset)
        print(model)
