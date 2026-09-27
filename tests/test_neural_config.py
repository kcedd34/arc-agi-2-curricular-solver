from src.solvers.neural.config import MAX_PREDICTIONS, NeuralSolverConfig


def test_defaults_match_adr_0055():
    config = NeuralSolverConfig()
    assert config.model_name == "Qwen/Qwen3-4B-Base"
    assert config.load_in_4bit is True
    assert config.num_predictions == MAX_PREDICTIONS


def test_geometric_augmentation_defaults_on():
    config = NeuralSolverConfig()
    assert config.use_geometric_augmentation is True


def test_lora_target_modules_are_not_shared_between_instances():
    a = NeuralSolverConfig()
    b = NeuralSolverConfig()
    a.lora_target_modules.append("mutated")
    assert "mutated" not in b.lora_target_modules


def test_color_augmentation_defaults_off_with_small_variant_count():
    config = NeuralSolverConfig()
    assert config.use_color_augmentation is False
    assert config.num_color_augmentations_per_pair == 2
    assert config.color_augmentation_seed == 42


def test_decoding_mitigation_defaults_are_neutral_hf_values():
    config = NeuralSolverConfig()
    assert config.repetition_penalty == 1.0
    assert config.no_repeat_ngram_size == 0
    assert config.stop_on_second_input is False
