import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from atlas_provider import MODEL_LITE, request_video, select_model


class FakeResponse:
    def __init__(self, payload):
        self.body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakeOpener:
    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    def __call__(self, request, **kwargs):
        self.calls.append((request, kwargs))
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def schema():
    return {
        "paths": {
            "/api/v1/model/generateVideo": {"x-api-name": "model_run"},
            "/api/v1/model/result/{request_id}": {"x-api-name": "model_result"},
        },
        "components": {
            "schemas": {
                "Input": {
                    "required": ["model", "prompt"],
                    "properties": {
                        "model": {"type": "string"},
                        "prompt": {"type": "string"},
                        "aspect_ratio": {"enum": ["16:9", "9:16"]},
                        "resolution": {"enum": ["720p", "1080p"]},
                        "duration": {"enum": [4, 6, 8]},
                        "seed": {"type": "integer"},
                    },
                }
            }
        },
    }


def discovery_results(*remaining):
    return (
        FakeResponse(
            {"data": [{"model": MODEL_LITE, "schema": "https://schema.test/veo.json"}]}
        ),
        FakeResponse(schema()),
        *remaining,
    )


class AtlasProviderTests(unittest.TestCase):
    def test_model_tiers_match_existing_flags(self):
        self.assertEqual(select_model(), "google/veo3.1-lite/text-to-video")
        self.assertEqual(select_model(force_pro=True), "google/veo3.1/text-to-video")
        self.assertEqual(
            select_model(force_fast=True), "google/veo3.1-fast/text-to-video"
        )

    def test_discovers_schema_submits_once_and_polls(self):
        opener = FakeOpener(
            *discovery_results(
                FakeResponse({"data": {"id": "video-1", "status": "processing"}}),
                FakeResponse(
                    {
                        "data": {
                            "id": "video-1",
                            "status": "completed",
                            "outputs": ["https://cdn.test/video.mp4"],
                        }
                    }
                ),
            )
        )

        output = request_video(
            "atlas-test",
            "a slow aerial pan",
            model=MODEL_LITE,
            aspect_ratio="16:9",
            resolution="720p",
            duration=4,
            opener=opener,
            sleep=lambda _seconds: None,
        )

        self.assertEqual(output, "https://cdn.test/video.mp4")
        post_calls = [call for call in opener.calls if call[0].get_method() == "POST"]
        self.assertEqual(len(post_calls), 1)

    def test_generation_post_failure_is_not_retried(self):
        opener = FakeOpener(
            *discovery_results(urllib.error.URLError("connection lost"))
        )

        with self.assertRaises(urllib.error.URLError):
            request_video(
                "atlas-test",
                "a slow aerial pan",
                model=MODEL_LITE,
                aspect_ratio="16:9",
                resolution="720p",
                duration=4,
                opener=opener,
            )

        post_calls = [call for call in opener.calls if call[0].get_method() == "POST"]
        self.assertEqual(len(post_calls), 1)

    def test_only_transient_prediction_get_is_retried(self):
        transient = urllib.error.HTTPError(
            "https://api.atlascloud.ai/result/video-2",
            503,
            "Service Unavailable",
            {},
            io.BytesIO(),
        )
        opener = FakeOpener(
            *discovery_results(
                FakeResponse({"data": {"id": "video-2", "status": "processing"}}),
                transient,
                FakeResponse(
                    {
                        "data": {
                            "id": "video-2",
                            "status": "completed",
                            "outputs": ["https://cdn.test/video.mp4"],
                        }
                    }
                ),
            )
        )
        sleep = mock.Mock()

        request_video(
            "atlas-test",
            "a slow aerial pan",
            model=MODEL_LITE,
            aspect_ratio="16:9",
            resolution="720p",
            duration=4,
            opener=opener,
            sleep=sleep,
        )

        sleep.assert_called_once_with(10.0)
        post_calls = [call for call in opener.calls if call[0].get_method() == "POST"]
        self.assertEqual(len(post_calls), 1)

    def test_invalid_resolution_is_rejected_before_generation_post(self):
        opener = FakeOpener(*discovery_results())

        with self.assertRaisesRegex(ValueError, "Invalid 'resolution'"):
            request_video(
                "atlas-test",
                "a slow aerial pan",
                model=MODEL_LITE,
                aspect_ratio="16:9",
                resolution="4k",
                duration=4,
                opener=opener,
            )

        self.assertFalse(any(call[0].get_method() == "POST" for call in opener.calls))


if __name__ == "__main__":
    unittest.main()
