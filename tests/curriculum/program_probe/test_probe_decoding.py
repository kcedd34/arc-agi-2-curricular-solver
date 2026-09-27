from src.curriculum.program_probe.decoding import comment_token_ids


class FakeTokenizer:
    vocab = ["a", " #", "##", "x#y", "\n"]

    def __len__(self):
        return len(self.vocab)

    def decode(self, ids):
        return "".join(self.vocab[i] for i in ids)


def test_every_token_containing_a_hash_is_forbidden():
    assert comment_token_ids(FakeTokenizer()) == [[1], [2], [3]]
