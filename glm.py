from transformers import AutoProcessor, AutoModelForImageTextToText, StoppingCriteria, StoppingCriteriaList, TextIteratorStreamer
import torch
import os
import threading
import time
from datetime import datetime
from PIL import Image

class AbortCriteria(StoppingCriteria):
    def __init__(self, abort_event):
        self.abort_event = abort_event

    def __call__(self, input_ids, scores, **kwargs):
        return self.abort_event.is_set()

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
        self.abort_event = threading.Event()
        print(f"Model loaded on {self.device}")

    def process_image(self, image_path, type="table"):
        # Reset abort event at start of processing
        self.abort_event.clear()
        
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
        
        stopping_criteria = StoppingCriteriaList([AbortCriteria(self.abort_event)])
        
        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs, 
                max_new_tokens=8192,
                stopping_criteria=stopping_criteria
            )
            
        if self.abort_event.is_set():
            print("Generation aborted by user.")
            return "<!-- Process Aborted -->"
            
        output_text = self.processor.decode(generated_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=False)
        return output_text

    def process_image_stream(self, image_path, type="table"):
        # Metrics initialization
        start_time = time.time()
        first_token_time = None
        full_text = ""
        
        # Get Image Dimensions
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                image_size_str = f"{height}x{width}"
        except Exception:
            image_size_str = "Unknown"

        # Reset abort event at start of processing
        self.abort_event.clear()
        
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
        
        streamer = TextIteratorStreamer(self.processor, skip_special_tokens=False, skip_prompt=True)
        stopping_criteria = StoppingCriteriaList([AbortCriteria(self.abort_event)])
        
        generation_kwargs = dict(
            **inputs,
            streamer=streamer,
            max_new_tokens=8192,
            stopping_criteria=stopping_criteria
        )

        thread = threading.Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()

        for new_text in streamer:
            if first_token_time is None:
                first_token_time = time.time()
            
            full_text += new_text

            if self.abort_event.is_set():
                print("Generation aborted by user.")
                yield "<!-- Process Aborted -->"
                break
            yield new_text
        
        # Calculations and Logging
        end_time = time.time()
        total_time = end_time - start_time
        
        if first_token_time:
            ttft = first_token_time - start_time
            generation_time = end_time - first_token_time
            
            # Count tokens (Approximate by re-tokenizing)
            # We use the processor's tokenizer
            token_ids = self.processor.tokenizer(full_text).input_ids
            token_count = len(token_ids)
            
            # TPS Calculation: (Total Tokens - 1) / Generation Time
            # We subtract 1 because the first token is generated at `first_token_time`
            # so the time period `generation_time` covers the generation of the remaining `N-1` tokens.
            if generation_time > 0 and token_count > 1:
                tps = (token_count - 1) / generation_time
            else:
                tps = 0.0
                
            print(f"\n[METRICS] Image: {image_size_str} | Mode: {type}")
            print(f"[METRICS] TTFT: {ttft:.4f}s | Total Time: {total_time:.4f}s")
            print(f"[METRICS] Tokens: {token_count} | TPS: {tps:.2f} tokens/s")
            
            # Log to file
            log_file = "performance.log"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = (
                f"[{timestamp}] Image: {image_size_str} | Mode: {type} | "
                f"TTFT: {ttft:.4f}s | Total: {total_time:.4f}s | "
                f"Tokens: {token_count} | TPS: {tps:.2f}\n"
            )
            try:
                with open(log_file, "a") as f:
                    f.write(log_entry)
            except Exception as e:
                print(f"Failed to write to {log_file}: {e}")
        else:
             print(f"\n[METRICS] No tokens generated. Total Time: {total_time:.4f}s")

if __name__ == "__main__":
    # Example usage mimicking original script
    ocr = GLMOCR()
    result = ocr.process_image("img.jpg")
    print(result)