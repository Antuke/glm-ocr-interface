from transformers import AutoProcessor, AutoModelForImageTextToText
import torch
import os

class GLMOCR:
    def __init__(self, model_path="zai-org/GLM-OCR", device="auto"):
        print(f"Loading model from {model_path}...")
        self.processor = AutoProcessor.from_pretrained(model_path)
        self.model = AutoModelForImageTextToText.from_pretrained(
            pretrained_model_name_or_path=model_path,
            torch_dtype="auto",
            device_map=device,
        )
        self.device = self.model.device
        print(f"Model loaded on {self.device}")

    def process_image(self, image_path, type="table"):
        table_prompt =  {
            "type": "table",
            "table": "Table Recognition:"
        }
        text_prompt = {
            "type": "text",
            "text": "Text Recognition:",
        }
        
        selected_prompt = table_prompt if type == "table" else text_prompt
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "url": image_path
                    },
                    selected_prompt
                ],
            }
        ]
        
        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt"
        ).to(self.device)
        
        inputs.pop("token_type_ids", None)
        
        with torch.no_grad():
            generated_ids = self.model.generate(**inputs, max_new_tokens=8192)
            
        output_text = self.processor.decode(generated_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=False)
        return output_text

if __name__ == "__main__":
    # Example usage mimicking original script
    ocr = GLMOCR()
    result = ocr.process_image("img.jpg")
    print(result)