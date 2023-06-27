from copy import deepcopy
import torch
import torchvision

mnist_train = torchvision.datasets.MNIST(
    "./files/",
    train=True,
    download=True,
    transform=torchvision.transforms.Compose(
        [
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize((0.1307,), (0.3081,)),
        ]
    ),
)

mnist_test = torchvision.datasets.MNIST(
    "./files/",
    train=False,
    download=True,
    transform=torchvision.transforms.Compose(
        [
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize((0.1307,), (0.3081,)),
        ]
    ),
)

train_dataset = mnist_train
test_dataset = mnist_test
batch_size = 64


def callable_to_initialize_collaborator_private_attributes(
    index, n_collaborators, batch_size, train_dataset, test_dataset
):
    train = deepcopy(train_dataset)
    test = deepcopy(test_dataset)
    train.data = train_dataset.data[index::n_collaborators]
    train.targets = train_dataset.targets[index::n_collaborators]
    test.data = test_dataset.data[index::n_collaborators]
    test.targets = test_dataset.targets[index::n_collaborators]

    return {
        "train_loader": torch.utils.data.DataLoader(
            train, batch_size=batch_size, shuffle=True
        ),
        "test_loader": torch.utils.data.DataLoader(
            test, batch_size=batch_size, shuffle=True
        ),
    }


def callable_to_initialize_aggregator_private_attributes(index):
    print("calling aggregator private attributes")