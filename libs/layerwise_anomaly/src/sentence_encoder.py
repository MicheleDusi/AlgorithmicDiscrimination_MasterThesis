############
# Code from: https://github.com/SPOClab-ca/layerwise-anomaly
# Li, B., Zhu, Z., Thomas, G., Xu, Y., and Rudzicz, F. (2021)
# How is BERT surprised? Layerwise detection of linguistic anomalies.
# In Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics (ACL).
############

from transformers import AutoTokenizer, AutoModel
import numpy as np
import torch
import string
import settings

BATCH_SIZE = 32


class SentenceEncoder:
    def __init__(self, model_name=settings.DEFAULT_BERT_MODEL_NAME):
        self.model_name = model_name
        self.auto_tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.auto_model = AutoModel.from_pretrained(model_name).to(settings.pt_device)
        self.pad_id = self.auto_tokenizer.pad_token_id

    def contextual_token_vecs(self, sentences, special_tokens: bool = True):
        """
        :param special_tokens: If True, special tokens such as [CLS] or [SEP] are included.
        :param sentences: The list of sentences
        :return: (all_tokens, sentence_token_vecs) where:
            all_tokens is a List[List[tokens]], one list for each sentence.
            sentence_token_vecs is List[np.array(sentence length, 13, 768)], one array for each sentence.
            Ignore special tokens like [CLS] and [PAD].
        """
        all_tokens = []
        sentence_token_vecs = []

        for batch_ix in range(0, len(sentences), BATCH_SIZE):
            batch_sentences = sentences[batch_ix: batch_ix + BATCH_SIZE]

            ids = torch.tensor(self.auto_tokenizer(batch_sentences, padding=True)['input_ids']).to(settings.pt_device)

            with torch.no_grad():
                # (num_layers, batch_size, sent_length, 768)
                vecs = self.auto_model(
                    ids,
                    attention_mask=(ids != self.pad_id).float(),
                    output_hidden_states=True)[2]
                vecs = np.array([v.detach().cpu().numpy() for v in vecs])

            for sent_ix in range(ids.shape[0]):
                tokens = []
                token_vecs = []

                for tok_ix in range(ids.shape[1]):
                    if ids[sent_ix, tok_ix] not in self.auto_tokenizer.all_special_ids or special_tokens:
                        cur_tok = self.auto_tokenizer.decode(int(ids[sent_ix, tok_ix]))
                        # Exclude tokens that consist entirely of punctuation
                        if cur_tok not in string.punctuation:
                            tokens.append(cur_tok)
                            token_vecs.append(vecs[:, sent_ix, tok_ix, :])

                all_tokens.append(tokens)
                sentence_token_vecs.append(np.array(token_vecs))

        return all_tokens, sentence_token_vecs
