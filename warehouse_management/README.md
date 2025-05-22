# Warehouse Management Extension

This module extends Odoo 17's warehouse management capabilities with advanced features for multi-company configurations, procurement workflows, inventory management, and geolocation-based logistics.

## Features

### 1. Restricted Subsidiary Purchases from External Vendors

Prevents subsidiary companies from creating Purchase Orders (POs) with external vendors, ensuring that only the parent company is authorized to procure from external sources.

**Implementation Details:**
- Validation mechanism during PO creation that checks the company type and vendor classification
- Error message if a subsidiary attempts to create a PO with an external vendor
- Configuration options in partner form to designate parent companies, subsidiaries, and external vendors

### 2. Enhanced Scrap Management with Categorization

Augments the existing scrap management process to include categorization of defective items and automated actions based on the category.

**Implementation Details:**
- Categorization of defective items into three types: 'Discard', 'Repair', and 'Return'
- Automated delivery order generation for items marked as 'Return'
- Notification system for responsible users
- Cost estimation for repair items
- Scrap categories configuration for standardized categorization

### 3. Automated Warehouse Selection Based on Customer Location

Automatically selects the warehouse closest to the customer's location for order fulfillment, optimizing delivery routes and improving efficiency.

**Implementation Details:**
- Geolocation-based distance calculation using the Haversine formula
- Automatic warehouse selection during sales order creation
- Consideration of stock availability in warehouses
- Prioritization based on distance and warehouse configuration
- User interface for visualizing GPS data and distances

## Configuration

### Company Configuration
1. Navigate to **Contacts** and open a partner record
2. Check the appropriate options:
   - "Is Parent Company" for the main company
   - "Is Subsidiary" for subsidiary companies (and select the parent company)
   - "Is External Vendor" for external suppliers

### Warehouse GPS Configuration
1. Navigate to **Inventory > Configuration > Warehouses**
2. Open a warehouse record and go to the "GPS Configuration" tab
3. Enter the latitude and longitude coordinates
4. Configure additional settings:
   - Enable/disable GPS routing
   - Set minimum stock percentage
   - Set priority for warehouse selection

### Scrap Categories
1. Navigate to **Inventory > Inventory Control > Scrap Categories**
2. Create or modify scrap categories with appropriate default actions

## Usage

### Purchase Order Restrictions
- When a subsidiary company user attempts to create a purchase order with an external vendor, they will receive an error message.
- Only users from the parent company can create purchase orders with external vendors.

### Scrap Management
1. Navigate to **Inventory > Operations > Scrap**
2. Create a new scrap record
3. Select the appropriate scrap type:
   - **Discard**: Items to be disposed of
   - **Repair**: Items to be repaired (will notify responsible person)
   - **Return**: Items to be returned (will automatically generate delivery order)
4. Fill in additional information based on the selected type
5. Confirm the scrap operation

### Automatic Warehouse Selection
1. Create a new sales order
2. Ensure the customer has GPS coordinates (can be added in the customer form)
3. The system will automatically select the closest warehouse for each product
4. Alternatively, click the "Select Nearest Warehouse" button to trigger manual selection
5. View the selected warehouses in the "Warehouse Selection" tab

## Technical Information

### Dependencies
- base
- purchase
- stock
- sale_management

### Models
- Extended: res.partner, purchase.order, stock.scrap, stock.warehouse, sale.order, sale.order.line
- New: stock.scrap.category

## Authors
- Your Company

## Maintainers
- Your Company
