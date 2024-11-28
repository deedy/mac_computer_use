import pytest
import asyncio
from computer_use.tools.mock_transformers import MockTransformersManager

@pytest.mark.asyncio
async def test_transformers_workflow():
    manager = MockTransformersManager()
    
    # Test loading model
    model_info = await manager.load_model("gpt2", "text-generation")
    assert model_info.model_id == "gpt2"
    assert model_info.task == "text-generation"
    
    # Test inference
    result = await manager.run_inference(
        "gpt2",
        "Hello, how are you?",
        max_length=50
    )
    assert result["model_id"] == "gpt2"
    assert "output" in result
    
    # Test getting loaded models
    models = manager.get_loaded_models()
    assert len(models) == 1
    assert models[0].model_id == "gpt2"
    
    # Test unloading model
    await manager.unload_model("gpt2")
    models = manager.get_loaded_models()
    assert len(models) == 0

if __name__ == "__main__":
    asyncio.run(test_transformers_workflow()) 