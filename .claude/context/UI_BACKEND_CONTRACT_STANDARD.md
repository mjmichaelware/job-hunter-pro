# UI Backend Contract Standard

Every UI surface must be backed by a real endpoint or labeled pending.

## For every UI element record

- visible label
- owning file
- renderer function
- endpoint
- HTTP method
- payload fields
- loading state
- empty state
- error state
- mobile behavior
- provider/cost risk

## For every backend endpoint record

- route
- method
- auth
- side effects
- cache behavior
- provider calls
- response schema
- frontend caller
- safe on page load
