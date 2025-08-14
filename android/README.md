# FitnessApp (Android)

Simple Jetpack Compose app with a yellow Material 3 theme that connects to your deployed backend.

Backend base URL: https://backend-45111119432.us-central1.run.app/

## Features
- Login via POST /login
- Data screen shows latest weight and recent activities
- Generate recipes via POST /generate-recipe

## Run
1. Open the `android/` folder in Android Studio Hedgehog or newer.
2. Let Gradle sync.
3. Run the `app` configuration on an emulator or device.

## Notes
- Endpoints expected from backend:
  - `POST /login` { email, password }
  - `GET /users/{id}/latest-weight`
  - `GET /activities?user_id={id}`
  - `POST /generate-recipe` { user_id, user_directions }
- CORS on the backend is open; mobile apps are fine.
- For demo credentials, seed users via backend CSV loader endpoints if needed.

