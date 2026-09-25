from django.test import SimpleTestCase
from unittest.mock import patch, Mock, MagicMock
from rest_framework.test import APIRequestFactory, force_authenticate

from .views import ScoreImageView, CompareImagesView, DetectIngredientsView
from .backend import OpenAIBackend, _parse_json_with_retry


class CookaiApiTests(SimpleTestCase):
	def setUp(self):
		self.factory = APIRequestFactory()
		# Minimal authenticated user mock
		self.user = Mock()
		self.user.is_authenticated = True

	@patch("cookai.models.AIRequestLog.objects.log", return_value=None)
	@patch("cookai.models.AIPrompt.objects.filter")
	@patch("cookai.backend.OpenAIBackend.score_images_detailed")
	def test_score_image_success_gpt5(self, mock_score, mock_prompt_filter, _mock_log):
		"""Test scoring with GPT-5 models"""
		mock_prompt_filter.return_value.first.return_value = None
		mock_score.return_value = {
			"overall_score": 88.5,
			"visual_appeal": 90.0,
			"cooking_technique": 85.0,
			"ingredient_freshness": 86.0,
			"ai_comment": "Excellent presentation!",
			"ai_summary": "Great dish!",
			"confidence": 0.95
		}
		
		view = ScoreImageView.as_view()
		request = self.factory.post("/api/cookai/score/", {"image": "http://example.com/foo.jpg"})
		force_authenticate(request, user=self.user)
		response = view(request)
		self.assertEqual(response.status_code, 200)
		self.assertIn("overall_score", response.data)
		self.assertIn("confidence", response.data)

	@patch("cookai.models.AIRequestLog.objects.log", return_value=None)
	@patch("cookai.models.AIPrompt.objects.filter")
	@patch("cookai.backend.OpenAIBackend.compare_images")
	def test_compare_images_success_gpt5(self, mock_cmp, mock_prompt_filter, _mock_log):
		"""Test comparison with GPT-5 models"""
		mock_prompt_filter.return_value.first.return_value = None
		mock_cmp.return_value = {"winner": 1, "reason": "Better plating and colors"}
		
		view = CompareImagesView.as_view()
		request = self.factory.post("/api/cookai/compare/", {"image1": "http://ex.com/a.jpg", "image2": "http://ex.com/b.jpg"})
		force_authenticate(request, user=self.user)
		response = view(request)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data.get("winner"), 1)

	@patch("cookai.models.AIRequestLog.objects.log", return_value=None)
	@patch("cookai.models.AIPrompt.objects.filter")
	@patch("cookai.backend.OpenAIBackend.detect_ingredients")
	def test_detect_success_gpt5(self, mock_detect, mock_prompt_filter, _mock_log):
		"""Test ingredient detection with GPT-5 models and retry mechanism"""
		mock_prompt_filter.return_value.first.return_value = None
		mock_detect.return_value = {
			"detected": ["tomato", "bell pepper"], 
			"match": True, 
			"confidence": 0.88, 
			"message": "✅ VISION QUEST COMPLETE! Found tomato and bell pepper!"
		}
		
		view = DetectIngredientsView.as_view()
		request = self.factory.post("/api/cookai/detect/", {"image_url": "http://ex.com/a.jpg", "target": ["tomato"]})
		force_authenticate(request, user=self.user)
		response = view(request)
		self.assertEqual(response.status_code, 200)
		body = response.data
		self.assertTrue(body["match"]) 
		self.assertIn("confidence", body)
		self.assertIn("message", body)
		self.assertIn("detected", body)

	def test_json_parsing_retry_mechanism(self):
		"""Test the new JSON parsing retry mechanism"""
		# Test valid JSON
		valid_json = '{"detected": ["tomato"], "match": true, "confidence": 0.9}'
		result = _parse_json_with_retry(valid_json)
		self.assertEqual(result["detected"], ["tomato"])
		
		# Test JSON wrapped in markdown
		markdown_json = '```json\n{"detected": ["pepper"], "match": false}\n```'
		result = _parse_json_with_retry(markdown_json)
		self.assertEqual(result["detected"], ["pepper"])
		
		# Test malformed JSON that should fail after retry
		with self.assertRaises(Exception):
			_parse_json_with_retry('not json at all')

	@patch("cookai.backend.client")
	def test_gpt5_model_selection(self, mock_client):
		"""Test GPT-5 model selection logic"""
		# Mock GPT-5 response
		mock_response = MagicMock()
		mock_response.output_text = '{"detected": ["tomato"], "match": true, "confidence": 0.95, "message": "Found tomato!"}'
		mock_client.responses.create.return_value = mock_response
		
		# Test model candidate selection
		candidates = OpenAIBackend._model_candidates("detect", preferred="gpt-5")
		self.assertIn("gpt-5", candidates)
		self.assertIn("gpt-5-mini", candidates)
		
		# Test that GPT-5 is preferred for detection
		self.assertEqual(candidates[0], "gpt-5")

	@patch("cookai.backend.OpenAIBackend._compress_image_for_api")
	def test_image_compression_integration(self, mock_compress):
		"""Test image compression integration"""
		mock_compress.return_value = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEA..."
		
		# Test that compression is called
		result = OpenAIBackend._prepare_image_reference("http://example.com/large_image.jpg")
		mock_compress.assert_called_once_with("http://example.com/large_image.jpg")
		self.assertTrue(result.startswith("data:image/jpeg;base64,"))

	@patch("cookai.models.AIRequestLog.objects.log", return_value=None)
	@patch("cookai.models.AIPrompt.objects.filter")
	@patch("cookai.backend.OpenAIBackend.detect_ingredients", side_effect=Exception("GPT-5 model error"))
	def test_detect_error_path_gpt5(self, mock_detect, mock_prompt_filter, _mock_log):
		"""Test error handling with GPT-5 models"""
		mock_prompt_filter.return_value.first.return_value = None
		view = DetectIngredientsView.as_view()
		request = self.factory.post("/api/cookai/detect/", {"image_url": "http://ex.com/a.jpg", "target": ["tomato"]})
		force_authenticate(request, user=self.user)
		response = view(request)
		self.assertEqual(response.status_code, 502)
		self.assertIn("detail", response.data)


class GPT5BackendTests(SimpleTestCase):
	"""Test GPT-5 specific backend functionality"""
	
	@patch("cookai.backend.OPENAI_API_KEY", "test-key")
	@patch("cookai.backend.client")
	def test_gpt5_responses_api_call(self, mock_client):
		"""Test GPT-5 Responses API calling logic"""
		# Mock the responses.create call
		mock_response = MagicMock()
		mock_response.output_text = '{"score": 85, "comment": "Great dish!"}'
		mock_client.responses.create.return_value = mock_response
		
		messages = [
			{"role": "system", "content": "You are a food critic"},
			{"role": "user", "content": "Rate this dish"}
		]
		
		result = OpenAIBackend._call_gpt5_responses_api(messages, "gpt-5")
		
		# Verify the API was called with correct parameters
		mock_client.responses.create.assert_called_once()
		call_args = mock_client.responses.create.call_args[1]
		self.assertEqual(call_args["model"], "gpt-5")
		self.assertIn("reasoning", call_args)
		self.assertIn("text", call_args)
		
		# Verify response format
		self.assertIn("choices", result)
		self.assertIn("message", result["choices"][0])
		self.assertIn("content", result["choices"][0]["message"])

	def test_model_candidates_prioritization(self):
		"""Test that GPT-5 models are properly prioritized"""
		# Test scoring scenario
		score_candidates = OpenAIBackend._model_candidates("score")
		self.assertEqual(score_candidates[0], "gpt-5")
		self.assertIn("gpt-5-mini", score_candidates)
		
		# Test detection scenario  
		detect_candidates = OpenAIBackend._model_candidates("detect")
		self.assertEqual(detect_candidates[0], "gpt-5")
		
		# Test comparison scenario
		compare_candidates = OpenAIBackend._model_candidates("compare")
		self.assertEqual(compare_candidates[0], "gpt-5")
