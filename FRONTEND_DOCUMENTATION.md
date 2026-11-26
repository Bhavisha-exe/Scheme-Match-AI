# SchemeMatch AI – Frontend Documentation

## 1. Overview
The frontend of SchemeMatch AI allows users to enter their personal details and receive government scheme recommendations based on the backend eligibility engine.

## 2. Technologies Used
- React.js
- Vite
- JavaScript
- HTML
- CSS

## 3. User Input Form
The form collects:
- Name
- Age
- State
- Annual family income
- Occupation
- Scheme category
- Gender

## 4. Backend Integration
The frontend sends user details to the backend using an HTTP POST request.

**API endpoint:**
`https://schemematch-backend.onrender.com/recommend`

**Request format:** JSON

The request includes age, income, occupation, state, category and gender.

## 5. Recommendation Results
The frontend displays:
- Scheme name
- Eligibility result
- Status
- Benefit details
- Matched conditions
- Unmet conditions

## 6. Error Handling
The frontend checks whether the backend request succeeds. If the backend cannot be reached or the request fails, an error message is displayed to the user.

## 7. Running the Frontend
1. Open the frontend folder in the terminal.
2. Run `npm install` if dependencies are not installed.
3. Run `npm run dev`.
4. Open the local URL displayed by Vite, usually `http://localhost:5173/`.

## 8. Testing
The frontend was tested for:
- Successful form submission and recommendation display.
- Display of matched and unmet eligibility conditions.
- Backend connection failure and error alert.
- Successful operation again after restoring the network connection.

## 9. Frontend Responsibilities
- Building the React user interface.
- Creating the user input form.
- Integrating the frontend with the backend API.
- Displaying scheme recommendations.
- Testing the user flow and error handling.
- Preparing frontend documentation and demo.
