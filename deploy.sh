#!/bin/bash

# Purpose: To deploy the App to Cloud Run.

# Google Cloud Project
#PROJECT=YOUR PROJECT ID

# Google Cloud Region
#LOCATION=us-central1

# Depolying app from source code
#gcloud run deploy simple-app --source . --region=$LOCATION --project=$PROJECT --allow-unauthenticated
gcloud run deploy simple-app --source . --region=us-central1 --project=YOUR-PROJECT-ID --allow-unauthenticated 
