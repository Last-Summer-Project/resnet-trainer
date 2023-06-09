from lightning import Trainer
from lightning.pytorch.tuner import Tuner
from lightning.pytorch.callbacks import ModelCheckpoint
from datamodule import SangchuDataModule
from model import ResNetClassifierModel
from cfg import Config
import torch


def main():
    # Tensor core test and set.
    if (
        torch.cuda.is_available()
        and torch.backends.cuda.matmul.allow_tf32 is False
        and torch.cuda.get_device_capability() >= (8, 0)
    ):
        torch.set_float32_matmul_precision("high")

    dm = SangchuDataModule()
    model = ResNetClassifierModel(Config.numClasses, Config.resnetVersion)

    checkpoint_last = ModelCheckpoint(filename="last", save_last=True)
    checkpoint_acc = ModelCheckpoint(
        filename="acc_best-{epoch}-{val_acc:.4f}",
        monitor="val_acc",
        mode="max",
        save_top_k=1,
    )
    checkpoint_loss = ModelCheckpoint(
        filename="loss_best-{epoch}-{val_loss:.4f}",
        monitor="val_loss",
        mode="min",
        save_top_k=1,
    )

    trainer = Trainer(
        max_epochs=Config.epochs,
        default_root_dir=Config.rootDir,
        callbacks=[checkpoint_last, checkpoint_acc, checkpoint_loss],
    )

    # autobatch
    try:
        if Config.autoBatch:
            tuner = Tuner(trainer)
            tuner.scale_batch_size(model, datamodule=dm, mode="power", max_trials=Config.batchMaxTries)
    except:
        pass

    trainer.fit(model, datamodule=dm)


if __name__ == "__main__":
    main()
