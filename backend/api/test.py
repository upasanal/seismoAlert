from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Earthquake Alert API"}

@app.get("/earthquake-alerts")
def get_earthquake_alerts():
    # Example: Fetch earthquake data from external API or database (Week 2)
    return {"alerts": "Thiss is where earthquake alertss will be displayed."}

