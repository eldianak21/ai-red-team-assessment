import torch
import torch.nn as nn


def fgsm_attack(model, image, label, epsilon=0.2, device="cpu"):
    """
    Fast Gradient Sign Method.

    image : (1, 1, 32, 32) tensor, values in [0, 1]
    label : (1,) tensor with the true class
    epsilon : perturbation strength
    """
    image = image.clone().detach().to(device)
    label = label.clone().detach().to(device)
    image.requires_grad = True

    output = model(image)
    loss = nn.NLLLoss()(output, label)
    model.zero_grad()
    loss.backward()

    perturbation = epsilon * image.grad.sign()
    adversarial = image + perturbation
    adversarial = torch.clamp(adversarial, 0.0, 1.0)
    return adversarial.detach()


def pgd_attack(model, image, label, epsilon=0.2, alpha=0.01, num_iter=40, device="cpu"):
    """
    Projected Gradient Descent.

    alpha : step size per iteration
    num_iter : number of iterations
    """
    image = image.clone().detach().to(device)
    label = label.clone().detach().to(device)
    original = image.clone().detach()

    adversarial = image.clone().detach()
    adversarial = adversarial + torch.empty_like(adversarial).uniform_(-epsilon, epsilon)
    adversarial = torch.clamp(adversarial, 0.0, 1.0)

    loss_fn = nn.NLLLoss()

    for _ in range(num_iter):
        adversarial.requires_grad = True
        output = model(adversarial)
        loss = loss_fn(output, label)
        model.zero_grad()
        loss.backward()

        grad = adversarial.grad.sign()
        adversarial = adversarial.detach() + alpha * grad

        delta = torch.clamp(adversarial - original, -epsilon, epsilon)
        adversarial = torch.clamp(original + delta, 0.0, 1.0).detach()

    return adversarial