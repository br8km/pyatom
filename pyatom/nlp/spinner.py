"""
    cls for text spinner
"""

import torch
from transformers import PegasusForConditionalGeneration, PegasusTokenizer

__all__ = ("Pegasus",)


class Pegasus:

    """
    Pegasus Paraphrase Generator:
        :https://huggingface.co/tuner007/pegasus_paraphrase
    """

    def __init__(self) -> None:
        """Init Spinner."""
        self.model_remote = "tuner007/pegasus_paraphrase"
        self.torch_device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = PegasusTokenizer.from_pretrained(self.model_remote)

        pegasus = PegasusForConditionalGeneration.from_pretrained(self.model_remote)
        if not pegasus:
            raise TypeError("PegasusForConditionGeneration is None!")

        self.model = pegasus.to(self.torch_device)

    def get_response(
        self, input_text: str, num_returns: int = 10, num_beams: int = 10
    ) -> list[str]:
        """Get list of paraphrase response for input text string."""
        num_returns = min(num_returns, num_beams)
        if not self.tokenizer:
            raise TypeError("PegasusTokenizer is None!")

        batch = self.tokenizer(
            [input_text],
            truncation=True,
            padding="longest",
            max_length=60,
            return_tensors="pt",
        ).to(self.torch_device)
        translated = self.model.generate(
            **batch,
            max_length=60,
            num_beams=num_beams,
            num_return_sequences=num_returns,
            temperature=1.5,
        )
        tgt_text = self.tokenizer.batch_decode(translated, skip_special_tokens=True)
        return [str(x) for x in tgt_text]

    def example(
        self, num_returns: int = 10, num_beams: int = 10, index: int = 0
    ) -> None:
        """Spin text demo."""
        context = "The ultimate test of your knowledge is your capacity to convey it to another."
        result = self.get_response(
            input_text=context, num_returns=num_returns, num_beams=num_beams
        )
        print(f"\n[{index}] - <{len(result)}>list of result:")
        for res in result:
            print(res)


class TestSpinner:
    """TestCase for Spinner."""

    @staticmethod
    def test_pegasus() -> None:
        """Test Pegasus."""
        app = Pegasus()
        num_returns = 10
        num_beams = 10

        context = "The ultimate test of your knowledge is your capacity to convey it to another."
        result = app.get_response(
            input_text=context, num_returns=num_returns, num_beams=num_beams
        )
        print(f"<{len(result)}>list of result:")
        for res in result:
            print(res)
            assert res


if __name__ == "__main__":
    TestSpinner()
