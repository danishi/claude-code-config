# Gemini Omni Flash prompt reference

Source: official guide "Generate and edit videos with Gemini Omni Flash"
(https://ai.google.dev/gemini-api/docs/omni, prompt guide section).

## 1. Single scene vs. multi-shot

By default the model builds a short narrative with several shots. For one take:

- `In a single unbroken scene`
- `In a single continuous shot`
- `No scene cuts`

```
Continuous, unbroken handheld shot of a fluffy tabby cat sitting on a sunny
windowsill, looking out into a leafy garden. The cat's tail twitches slowly,
and its ears rotate slightly toward ambient noises. Sunbeams illuminate dust
motes in the air. Sound design: Gentle breeze, distant bird chirps. No dialogue.
```

## 2. Removing unwanted elements

Negative prompts are not a parameter; write them as plain sentences:

- `No dialogue`
- `No embellishments`
- `No extra sound effects`

## 3. Editing prompts — keep them short

| Avoid | Simplify |
|---|---|
| In the video of the man sitting on the sofa, please add a small black cat that runs from the right side of the screen, jumps onto his lap, and then he starts to stroke its head while looking down. | Add a cat that jumps onto his lap, he begins to pet it. Keep everything else the same. |
| Please remove the cell phone that the person is holding in their hand and fill in the background so it looks like they are just holding their hand empty. | Make the phone invisible. Keep everything else the same. |

More short edits:

- `Make this video anime`
- `Put a fashionable hat on this person`
- `Change the lighting to be more dramatic`
- `Change the text on the sign to say "Omni Flash"`

## 4. Audio

The model generates a soundtrack on its own. Describe it when it matters, especially music:

- `Include calm background music`
- `The video has a high energy techno beat`
- `The audio is a low tinny radio broadcast in the background, playing a song`
- Dialogue: `She says: "We made it."` (quote the exact line)

## 5. Timing events

Natural language works:

- `After 3 seconds, a woman enters the scene.`
- `At 5s the chorus starts in the background audio.`
- `Every 2s cut to a new frame.`
- `In a rapid fire sequence, every half a second (12 frames at 24fps) change the scene to a new location.`

Timecodes also work:

```
[0-3s] A person is walking
[3-6s] They stop and turn around
[6-10s] They start running
```

## 6. Meta prompting

- `Consider micro-detail, expression and timing to create a very rich, detailed but entirely natural scene.`
- `Be extremely detailed in your descriptions of characters and environments. Apply costume design principles to characters.`
- `Include plenty of appropriate detail in the background elements to make the scene feel realistic and natural.`
- `Make a rapid fire video that shows a different rare [thing] every 1s, upbeat music, include text to label the thing.`

## 7. Text in videos

On-screen text renders legibly. Spell out any text that will appear, even background signs:

- `One word on the screen at a time: "did, you, know, that, Omni, can, do, awesome, text?" Each word appears for 1s with a different animated style. No dialogue.`
- `There is a street sign that says: "This is an AI generation by Omni", a storefront that says: "All you need AI", a car with the number plate: "OMNI1.1"`

## 8. Extending a video

- `Extend this video` / `The scene continues` — adds ~10s per turn, up to 40s total.
- The last 10s of the input are used as context; a few final frames are re-rendered for a seamless join.
- Describe audio changes: `The music continues into the chorus`
- Say whether it is the same shot or a cut: `Show the same characters in the next scene`
- Add reference images to introduce characters: `The person shown in the reference image enters the scene`
- Timestamps restart at the extension: `After 2s cut to a new scene` = 2s after the original end.

## 9. Image-to-video

- Use high-resolution images.
- State how the image is used: `use the drawing only as a guide for movement, do not show the drawing in the final video`.
- Describe camera movement, subject motion and environmental effects; `make it move` is too vague.

## Templates

**Product shot (image-to-video)**
```
Bring this product photo to life: slow 360-degree orbit around the product on a
glossy surface, soft studio lighting with moving reflections. Continuous single
shot. Sound design: subtle whoosh, minimal electronic music. No dialogue.
```

**Explainer with on-screen text**
```
[0-3s] Title card that says "3 tips for better sleep", clean motion graphics.
[3-6s] "1. No screens before bed" with a phone fading out.
[6-9s] "2. Keep it cool" with a thermometer dropping.
[9-10s] "3. Same time every day" with a clock. Calm piano music. No dialogue.
```

**Short drama with dialogue**
```
A rainy Tokyo alley at night, neon reflections in puddles. A detective in a
trench coat lights a match and says: "It ends tonight." Cinematic, 35mm film
look, slow push-in. Sound: rain, distant traffic, low synth drone.
```
