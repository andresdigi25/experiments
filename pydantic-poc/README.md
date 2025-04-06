# Pydantic Example Project

This project demonstrates how to use Pydantic for data validation and settings management in Python, showcasing both Pydantic v1 and v2.

## Project Structure

```
pydantic-example
├── pydantic_v1
│   ├── main.py        # Entry point for Pydantic v1 example
│   └── models.py      # User model definition for Pydantic v1
├── pydantic_v2
│   ├── main.py        # Entry point for Pydantic v2 example
│   └── models.py      # User model definition for Pydantic v2
└── README.md          # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd pydantic-example
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Pydantic:**
   For Pydantic v1:
   ```
   pip install pydantic==1.*
   ```

   For Pydantic v2:
   ```
   pip install pydantic==2.*
   ```

## Running the Examples

### Pydantic v1

To run the Pydantic v1 example, navigate to the `pydantic_v1` directory and execute:

```
python main.py
```

### Pydantic v2

To run the Pydantic v2 example, navigate to the `pydantic_v2` directory and execute:

```
python main.py
```

## License

This project is licensed under the MIT License.