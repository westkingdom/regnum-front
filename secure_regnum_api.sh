#!/bin/bash

# Script to secure regnum-api for service-to-service communication
# Multiple security options available

set -e

PROJECT_ID=$(gcloud config get-value project)
REGION="us-west1"
API_SERVICE="regnum-api"
FRONT_SERVICE="regnum-front"

echo "🔒 Securing regnum-api for service-to-service communication"
echo "=================================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "API Service: $API_SERVICE"
echo "Frontend Service: $FRONT_SERVICE"
echo ""

# Function to show menu
show_menu() {
    echo "Choose security option:"
    echo "1. Service-to-Service Authentication (Recommended)"
    echo "2. VPC Network Security (Advanced)"
    echo "3. Custom Service Account (Most Secure)"
    echo "4. Show Current Status"
    echo "5. Test Connection"
    echo "6. Revert to Public Access"
    echo "0. Exit"
}

# Function to implement service-to-service authentication
setup_service_auth() {
    echo "🔧 Setting up service-to-service authentication..."
    
    # Step 1: Remove public access from regnum-api
    echo "1. Removing public access from regnum-api..."
    gcloud run services remove-iam-policy-binding $API_SERVICE \
        --region=$REGION \
        --member="allUsers" \
        --role="roles/run.invoker" \
        --quiet 2>/dev/null || echo "   No public access to remove"

    # Step 2: Get the service account used by regnum-front
    echo "2. Getting regnum-front service account..."
    REGNUM_FRONT_SA=$(gcloud run services describe $FRONT_SERVICE \
        --region=$REGION \
        --format="value(spec.template.spec.serviceAccountName)" 2>/dev/null)

    if [ -z "$REGNUM_FRONT_SA" ] || [ "$REGNUM_FRONT_SA" = "null" ]; then
        echo "   regnum-front uses default Compute Engine service account"
        REGNUM_FRONT_SA="${PROJECT_ID}-compute@developer.gserviceaccount.com"
    fi

    echo "   Service Account: $REGNUM_FRONT_SA"

    # Step 3: Grant regnum-front service account permission to invoke regnum-api
    echo "3. Granting regnum-front permission to invoke regnum-api..."
    gcloud run services add-iam-policy-binding $API_SERVICE \
        --region=$REGION \
        --member="serviceAccount:$REGNUM_FRONT_SA" \
        --role="roles/run.invoker"

    echo ""
    echo "✅ Service-to-service authentication configured!"
    echo "   Only regnum-front can access regnum-api"
    echo "   Public access has been removed"
}

# Function to create custom service account
setup_custom_service_account() {
    echo "🔧 Setting up custom service account..."
    
    SA_NAME="regnum-front-sa"
    SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
    
    # Create service account
    echo "1. Creating custom service account..."
    gcloud iam service-accounts create $SA_NAME \
        --display-name="Regnum Front Service Account" \
        --description="Service account for regnum-front to access regnum-api" \
        2>/dev/null || echo "   Service account already exists"
    
    # Remove public access from regnum-api
    echo "2. Removing public access from regnum-api..."
    gcloud run services remove-iam-policy-binding $API_SERVICE \
        --region=$REGION \
        --member="allUsers" \
        --role="roles/run.invoker" \
        --quiet 2>/dev/null || echo "   No public access to remove"
    
    # Grant custom service account permission to invoke regnum-api
    echo "3. Granting custom service account permission to invoke regnum-api..."
    gcloud run services add-iam-policy-binding $API_SERVICE \
        --region=$REGION \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/run.invoker"
    
    # Update regnum-front to use the custom service account
    echo "4. Updating regnum-front to use custom service account..."
    gcloud run services update $FRONT_SERVICE \
        --region=$REGION \
        --service-account=$SA_EMAIL
    
    echo ""
    echo "✅ Custom service account configured!"
    echo "   Service Account: $SA_EMAIL"
    echo "   regnum-front now uses dedicated service account"
    echo "   Only this service account can access regnum-api"
}

# Function to show current status
show_status() {
    echo "📊 Current Security Status"
    echo "========================="
    
    echo ""
    echo "🔍 regnum-api IAM Policy:"
    gcloud run services get-iam-policy $API_SERVICE --region=$REGION --format="table(bindings.members,bindings.role)" 2>/dev/null || echo "   Error getting IAM policy"
    
    echo ""
    echo "🔍 regnum-front Service Account:"
    FRONT_SA=$(gcloud run services describe $FRONT_SERVICE --region=$REGION --format="value(spec.template.spec.serviceAccountName)" 2>/dev/null)
    if [ -z "$FRONT_SA" ] || [ "$FRONT_SA" = "null" ]; then
        echo "   Uses default Compute Engine service account"
    else
        echo "   $FRONT_SA"
    fi
    
    echo ""
    echo "🔍 Service URLs:"
    echo "   regnum-api: $(gcloud run services describe $API_SERVICE --region=$REGION --format="value(status.url)" 2>/dev/null)"
    echo "   regnum-front: $(gcloud run services describe $FRONT_SERVICE --region=$REGION --format="value(status.url)" 2>/dev/null)"
}

# Function to test connection
test_connection() {
    echo "🧪 Testing Connection"
    echo "==================="
    
    API_URL=$(gcloud run services describe $API_SERVICE --region=$REGION --format="value(status.url)" 2>/dev/null)
    
    echo "Testing public access to regnum-api..."
    if curl -s -o /dev/null -w "%{http_code}" "${API_URL}/groups/" | grep -q "200"; then
        echo "❌ regnum-api is publicly accessible"
    else
        echo "✅ regnum-api is not publicly accessible"
    fi
    
    echo ""
    echo "To test authenticated access, deploy regnum-front and check the logs:"
    echo "gcloud logs read --service=$FRONT_SERVICE --limit=10"
}

# Function to revert to public access
revert_to_public() {
    echo "⚠️  Reverting to public access..."
    
    gcloud run services add-iam-policy-binding $API_SERVICE \
        --region=$REGION \
        --member="allUsers" \
        --role="roles/run.invoker"
    
    echo "✅ regnum-api is now publicly accessible"
}

# Main menu loop
while true; do
    echo ""
    show_menu
    read -p "Enter your choice (0-6): " choice
    
    case $choice in
        1)
            setup_service_auth
            ;;
        2)
            echo "VPC Network Security requires additional setup."
            echo "This involves creating a VPC connector and configuring network policies."
            echo "Contact your cloud administrator for VPC setup."
            ;;
        3)
            setup_custom_service_account
            ;;
        4)
            show_status
            ;;
        5)
            test_connection
            ;;
        6)
            read -p "Are you sure you want to make regnum-api publicly accessible? (y/N): " confirm
            if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                revert_to_public
            fi
            ;;
        0)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid choice. Please try again."
            ;;
    esac
done

