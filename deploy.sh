#!/bin/bash

# Purpose: To deploy the App to Cloud Run.

# Google Cloud Project
PROJECT=test-metal-358914

# Google Cloud Region
LOCATION=us-central1

# Depolying app from source code
#gcloud run deploy simple-app --source . --region=$LOCATION --project=$PROJECT --allow-unauthenticated
gcloud run deploy simple-app --source . --region=us-central1 --project=test-metal-358914 --allow-unauthenticated 
gcloud run deploy simple-app \
  --source . \
  --region=us-central1 \
  --project=test-metal-358914 \
  --cpu=4 \
  --memory=2Gi \
  --allow-unauthenticated