import torch
from torch.autograd import Variable
import numpy as np
import torch.nn.functional as F


def sequence_mask(sequence_length, max_len=None, use_cuda=False):
    if isinstance(sequence_length, np.ndarray):
        sequence_length = Variable(torch.from_numpy(sequence_length))
    elif isinstance(sequence_length, list):
        sequence_length = Variable(torch.from_numpy(np.array(sequence_length)))

    if max_len is None:
        max_len = sequence_length.data.max()

    batch_size = sequence_length.size(0)
    seq_range = torch.arange(0, max_len).long()
    seq_range_expand = seq_range.unsqueeze(0).expand(batch_size, max_len)
    seq_range_expand = Variable(seq_range_expand)
    if sequence_length.is_cuda:
        seq_range_expand = seq_range_expand.cuda()
    seq_length_expand = (sequence_length.unsqueeze(1)
                         .expand_as(seq_range_expand))
    mask = seq_range_expand < seq_length_expand
    if use_cuda:
        mask = mask.cuda()
    return mask


def masked_cross_entropy(logits, target, length, use_cuda=False):

    length = Variable(torch.LongTensor(length))

    if use_cuda:
        length = length.cuda()

    """
        Args:
        logits: A Variable containing a FloatTensor of size
        (batch, max_len, num_classes) which contains the
        unnormalized probability for each class.
        target: A Variable containing a LongTensor of size
        (batch, max_len) which contains the index of the true
        class for each corresponding step.
        length: A Variable containing a LongTensor of size (batch,)
        which contains the length of each data in a batch.
        Returns:
        loss: An average loss value masked by the length.
        """
    
    # logits_flat: (batch * max_len, num_classes)
    logits_flat = logits.view(-1, logits.size(-1))
    # log_probs_flat: (batch * max_len, num_classes)
    log_probs_flat = F.log_softmax(logits_flat)
    # target_flat: (batch * max_len, 1)
    target_flat = target.view(-1, 1)
    # losses_flat: (batch * max_len, 1)
    losses_flat = -torch.gather(log_probs_flat, dim=1, index=target_flat)
    # losses: (batch, max_len)
    losses = losses_flat.view(*target.size())
    # mask: (batch, max_len)
    mask = sequence_mask(sequence_length=length, max_len=target.size(1), use_cuda=use_cuda)
    losses = losses * mask.float()
    loss = losses.sum() / length.float().sum()
    return loss
