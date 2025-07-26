# Bruno AI V3.1 Fullstack Architecture Document

## 1. Introduction

This document outlines the complete fullstack architecture for Bruno AI V3.1, including backend systems, frontend implementation, and their integration. It serves as the single source of truth for AI-driven development, ensuring consistency across the entire technology stack.

This unified approach combines what would traditionally be separate backend and frontend architecture documents, streamlining the development process for modern fullstack applications where these concerns are increasingly intertwined.

### 1.1. Starter Template or Existing Project

N/A - Greenfield project.

**Rationale:** This decision was made based on a SWOT analysis. A greenfield approach provides the necessary flexibility for the project's unique and modern technology stack (Flutter, FastAPI, CrewAI, etc.), avoiding the high customization overhead and potential architectural conflicts of adapting a generic starter template. This ensures the architecture is purpose-built for the project's specific needs.

### 1.2. Change Log

| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| | | | |

---

## 2. High Level Architecture

### 2.1. Technical Summary

The architecture for Bruno AI V3.1 is designed as a modern, scalable, and cost-efficient full-stack application. It leverages a serverless-first approach on Google Cloud Platform (GCP) to maximize price-performance. The frontend is a Flutter mobile application, communicating with a Python FastAPI backend deployed as a container on Cloud Run. The core business logic is powered by a sophisticated multi-agent AI system orchestrated by CrewAI. A monorepo structure will be used to ensure code consistency and streamline development across the stack, with a centralized repository pattern for clean data access and component-based UI for a maintainable frontend.

### 2.2. Platform and Infrastructure Choice

*   **Platform:** Google Cloud Platform (GCP)
*   **Key Services:** Cloud Run, Cloud SQL (PostgreSQL), Cloud Storage, Firebase Authentication, Vertex AI
*   **Deployment Host and Regions:** To be determined, likely starting with a single region in North America (e.g., `us-central1`).

### 2.3. Repository Structure

*   **Structure:** Monorepo
*   **Monorepo Tool:** Nx (This provides robust support for multi-language projects, including Flutter and Python, and helps manage shared dependencies and build scripts effectively).
*   **Package Organization:** The repository will be organized into `apps` (for the Flutter client and FastAPI server) and `packages` (for shared code like data models and types).

### 2.4. High Level Architecture Diagram

```mermaid
graph TD
    subgraph User
        A[Mobile User]
    end

    subgraph GCP
        B[Flutter App on Mobile] --> C{API Gateway};
        C --> D[Cloud Run: FastAPI Backend];
        D --> E[Cloud SQL: PostgreSQL Database];
        D --> F[Cloud Storage: Files/Assets];
        D --> G((CrewAI Multi-Agent System));
        G --> H{LLMs: GPT-4.1 etc.};
        G --> I[Mem0: Memory Layer];
        B --> J[Firebase Authentication];
    end

    subgraph External Services
        G --> K[Instacart API];
        G --> L[Voxtral STT API];
    end

    A --> B;
```

### 2.5. Architectural Patterns

*   **Serverless Architecture:** The backend will be deployed as a stateless container on Google Cloud Run, enabling automatic scaling (including to zero) to maximize cost-efficiency. - *Rationale:* Aligns with our primary goal of price-performance and reduces operational overhead.
*   **Repository Pattern:** A data access layer will abstract all database interactions, separating business logic from data storage concerns. - *Rationale:* Improves testability, maintainability, and allows for future database flexibility.
*   **Component-Based UI with Centralized State Management:** The Flutter app will be built from reusable widgets with a central state management solution (e.g., BLoC) to ensure a predictable and maintainable UI. - *Rationale:* Standard best practice for modern UI development, promoting reusability and scalability.
*   **Multi-Agent System:** The core application intelligence will be orchestrated by the CrewAI framework, as required by the PRD. - *Rationale:* This is a core product differentiator and is essential for handling complex, collaborative user requests.

---

## 3. Tech Stack

### 3.1. Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend Language** | Dart | Latest Stable | Language for Flutter | Required by the Flutter framework. |
| **Frontend Framework** | Flutter | Latest Stable | Cross-platform mobile UI | As specified in the PRD for building the mobile application. |
| **UI Component Library**| Material Design | (Bundled) | Core UI components | Flutter's native, high-quality component library. |
| **State Management** | Flutter BLoC | Latest | Predictable state management | Robust, scalable, and separates business logic from UI. |
| **Backend Language** | Python | 3.11+ | Backend development | As specified in the PRD; excellent for AI/ML and web services. |
| **Backend Framework** | FastAPI | Latest | High-performance API creation | As specified in the PRD; modern, fast, with automatic docs. |
| **ORM** | SQLAlchemy | Latest | Data Access Layer | Industry standard for Python, simplifies database interactions. |
| **API Style** | REST | (OpenAPI 3.0) | Client-server communication | Simple, well-understood, and supported by FastAPI. |
| **Database** | PostgreSQL | Latest Stable | Relational data storage | As specified in the PRD; powerful, reliable, and open-source. |
| **File Storage** | Google Cloud Storage | N/A | Storing user assets | Secure, scalable, and integrates perfectly with our GCP stack. |
| **Authentication** | Firebase Auth | N/A | User identity management | Secure, easy to implement, and cost-effective. |
| **AI Orchestration** | CrewAI, RouteLLM, Mem0 | Latest | Core AI functionality | As explicitly required by the PRD for the multi-agent system. |
| **Voice (STT)** | Voxtral API | Latest | Speech-to-Text | As specified in the PRD for voice interaction. |
| **Containerization** | Docker | Latest | Backend packaging | Essential for deploying our FastAPI app to Google Cloud Run. |
| **IaC Tool** | Terraform | Latest | Infrastructure management | Defines our GCP resources as code for consistency and safety. |
| **CI/CD** | GitHub Actions | N/A | Automated build & deploy | Native to our likely code host, powerful and flexible. |
| **Backend Testing** | Pytest | Latest | Unit & integration tests | The standard, powerful testing framework for Python. |
| **Frontend Testing** | flutter_test | (Bundled) | Unit & widget tests | Flutter's built-in, comprehensive testing suite. |

---

## 4. Data Models

### 4.1. User

**Purpose:** Represents an individual user of the application. This model stores authentication details, personal information, and application-specific preferences like dietary needs and voice settings. It is the central anchor for user-specific data.

**Key Attributes:**
*   `id`: `UUID` - Unique identifier for the user.
*   `email`: `String` - User's email address, used for login. Must be unique.
*   `name`: `String` - User's display name.
*   `voice_settings`: `JSON` - Stores user-specific voice preferences (e.g., voice type, speed).
*   `dietary_preferences`: `JSON` - Stores user's dietary restrictions and preferences (e.g., vegan, gluten-free).
*   `created_at`: `DateTime` - Timestamp of when the user account was created.
*   `updated_at`: `DateTime` - Timestamp of the last update to the user's record.

**Relationships:**
*   **One-to-Many:** A `User` can place multiple `Orders`.
*   **Many-to-One:** A `User` belongs to one `Household`.

---
#### Backend Model (Python/Pydantic)
```python
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Dict, Any

class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    name: str
    voice_settings: Dict[str, Any] = {}
    dietary_preferences: Dict[str, Any] = {}
    household_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True
```

#### Frontend Model (Dart)
```dart
import 'package:uuid/uuid.dart';

class User {
  final String id;
  final String email;
  final String name;
  final Map<String, dynamic> voiceSettings;
  final Map<String, dynamic> dietaryPreferences;
  final String? householdId;
  final DateTime createdAt;
  final DateTime updatedAt;

  User({
    required this.id,
    required this.email,
    required this.name,
    required this.voiceSettings,
    required this.dietaryPreferences,
    this.householdId,
    required this.createdAt,
    required this.updatedAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
      name: json['name'],
      voiceSettings: json['voice_settings'] ?? {},
      dietaryPreferences: json['dietary_preferences'] ?? {},
      householdId: json['household_id'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'name': name,
      'voice_settings': voiceSettings,
      'dietary_preferences': dietaryPreferences,
      'household_id': householdId,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}
```
---

### 4.2. Household

**Purpose:** Represents a shared space for a group of users (e.g., a family). It contains the shared pantry, shopping lists, and manages member permissions. This model is the key to enabling real-time collaboration.

**Key Attributes:**
*   `id`: `UUID` - Unique identifier for the household.
*   `name`: `String` - The name of the household (e.g., "The Smiths' Home").
*   `admin_user_id`: `UUID` - The `id` of the user who created and manages the household.
*   `invite_code`: `String` - A simple, short-lived code used to invite new members.
*   `created_at`: `DateTime` - Timestamp of when the household was created.
*   `updated_at`: `DateTime` - Timestamp of the last update.

**Relationships:**
*   **One-to-Many:** A `Household` has many `Users`.
*   **One-to-Many:** A `Household` has many `PantryItems`.
*   **One-to-Many:** A `Household` has many `ShoppingLists`.

---
#### Backend Model (Python/Pydantic)
```python
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from typing import List

class Household(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    admin_user_id: UUID
    invite_code: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True
```

#### Frontend Model (Dart)
```dart
import 'package:uuid/uuid.dart';

class Household {
  final String id;
  final String name;
  final String adminUserId;
  final String inviteCode;
  final DateTime createdAt;
  final DateTime updatedAt;

  Household({
    required this.id,
    required this.name,
    required this.adminUserId,
    required this.inviteCode,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Household.fromJson(Map<String, dynamic> json) {
    return Household(
      id: json['id'],
      name: json['name'],
      adminUserId: json['admin_user_id'],
      inviteCode: json['invite_code'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'admin_user_id': adminUserId,
      'invite_code': inviteCode,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}
```
---

### 4.3. PantryItem

**Purpose:** Represents a single item within a household's shared pantry. This model tracks the item's details, quantity, and, most importantly, its expiration date to power the smart warning features.

**Key Attributes:**
*   `id`: `UUID` - Unique identifier for the pantry item.
*   `household_id`: `UUID` - The `id` of the household this item belongs to.
*   `name`: `String` - The name of the item (e.g., "Milk", "Eggs").
*   `quantity`: `Float` - The amount of the item (e.g., 1.5, 12). Using float for flexibility (e.g., 1.5 liters).
*   `unit`: `String` - The unit of measurement (e.g., "liters", "carton", "grams").
*   `expiration_date`: `Date` - The expiration date of the item. Nullable for non-perishable items.
*   `category`: `String` - The category of the item (e.g., "Dairy", "Produce", "Pantry Staples").
*   `added_by_user_id`: `UUID` - The `id` of the user who added the item.
*   `created_at`: `DateTime` - Timestamp of when the item was added.
*   `updated_at`: `DateTime` - Timestamp of the last update.

**Relationships:**
*   **Many-to-One:** Many `PantryItems` belong to one `Household`.
*   **Many-to-One:** Many `PantryItems` can be added by one `User`.

---
#### Backend Model (Python/Pydantic)
```python
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, date
from typing import Optional

class PantryItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    household_id: UUID
    name: str
    quantity: float
    unit: str
    expiration_date: Optional[date] = None
    category: str
    added_by_user_id: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True
```

#### Frontend Model (Dart)
```dart
import 'package:uuid/uuid.dart';

class PantryItem {
  final String id;
  final String householdId;
  final String name;
  final double quantity;
  final String unit;
  final DateTime? expirationDate;
  final String category;
  final String addedByUserId;
  final DateTime createdAt;
  final DateTime updatedAt;

  PantryItem({
    required this.id,
    required this.householdId,
    required this.name,
    required this.quantity,
    required this.unit,
    this.expirationDate,
    required this.category,
    required this.addedByUserId,
    required this.createdAt,
    required this.updatedAt,
  });

  factory PantryItem.fromJson(Map<String, dynamic> json) {
    return PantryItem(
      id: json['id'],
      householdId: json['household_id'],
      name: json['name'],
      quantity: (json['quantity'] as num).toDouble(),
      unit: json['unit'],
      expirationDate: json['expiration_date'] != null
          ? DateTime.parse(json['expiration_date'])
          : null,
      category: json['category'],
      addedByUserId: json['added_by_user_id'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'household_id': householdId,
      'name': name,
      'quantity': quantity,
      'unit': unit,
      'expiration_date': expirationDate?.toIso8601String().split('T').first,
      'category': category,
      'added_by_user_id': addedByUserId,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}
```
---

### 4.4. Recipe

**Purpose:** Represents a recipe that can be suggested to users based on their pantry contents. This model will store the recipe's instructions, ingredients, and other relevant information like preparation time and nutritional details.

**Key Attributes:**
*   `id`: `UUID` - Unique identifier for the recipe.
*   `name`: `String` - The name of the recipe.
*   `instructions`: `Text` - The step-by-step instructions for preparing the meal.
*   `ingredients`: `JSON` - A structured list of ingredients, including quantity and unit (e.g., `[{ "name": "Flour", "quantity": 2, "unit": "cups" }]`).
*   `prep_time`: `Integer` - The preparation time in minutes.
*   `servings`: `Integer` - The number of servings the recipe makes.
*   `nutrition_info`: `JSON` - Nutritional information per serving (e.g., calories, protein, fat).
*   `created_at`: `DateTime` - Timestamp of when the recipe was added.
*   `updated_at`: `DateTime` - Timestamp of the last update.

**Relationships:**
*   This is a standalone model for now. In the future, it could be linked to users for "favorite recipes" or to a `MealPlan` model.

---
#### Backend Model (Python/Pydantic)
```python
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from typing import List, Dict, Any

class Ingredient(BaseModel):
    name: str
    quantity: float
    unit: str

class Recipe(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    instructions: str
    ingredients: List[Ingredient]
    prep_time: int
    servings: int
    nutrition_info: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True
```

#### Frontend Model (Dart)
```dart
import 'package:uuid/uuid.dart';

class Ingredient {
  final String name;
  final double quantity;
  final String unit;

  Ingredient({
    required this.name,
    required this.quantity,
    required this.unit,
  });

  factory Ingredient.fromJson(Map<String, dynamic> json) {
    return Ingredient(
      name: json['name'],
      quantity: (json['quantity'] as num).toDouble(),
      unit: json['unit'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'quantity': quantity,
      'unit': unit,
    };
  }
}

class Recipe {
  final String id;
  final String name;
  final String instructions;
  final List<Ingredient> ingredients;
  final int prepTime;
  final int servings;
  final Map<String, dynamic> nutritionInfo;
  final DateTime createdAt;
  final DateTime updatedAt;

  Recipe({
    required this.id,
    required this.name,
    required this.instructions,
    required this.ingredients,
    required this.prepTime,
    required this.servings,
    required this.nutritionInfo,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Recipe.fromJson(Map<String, dynamic> json) {
    var ingredientsList = json['ingredients'] as List;
    List<Ingredient> ingredients = ingredientsList.map((i) => Ingredient.fromJson(i)).toList();

    return Recipe(
      id: json['id'],
      name: json['name'],
      instructions: json['instructions'],
      ingredients: ingredients,
      prepTime: json['prep_time'],
      servings: json['servings'],
      nutritionInfo: json['nutrition_info'] ?? {},
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'instructions': instructions,
      'ingredients': ingredients.map((i) => i.toJson()).toList(),
      'prep_time': prepTime,
      'servings': servings,
      'nutrition_info': nutritionInfo,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}
```
---

### 4.5. Shopping List

**Purpose:** Represents a collaborative list of items to be purchased. Users within a household can add items to this list, and it will be used to generate orders through services like Instacart.

**Key Attributes:**
*   `id`: `UUID` - Unique identifier for the shopping list.
*   `household_id`: `UUID` - The `id` of the household this shopping list belongs to.
*   `name`: `String` - The name of the shopping list (e.g., "Weekly Groceries", "Party Supplies").
*   `items`: `JSON` - A structured list of items to be purchased, including quantity and notes (e.g., `[{ "name": "Milk", "quantity": 1, "unit": "gallon", "notes": "2% organic" }]`).
*   `status`: `String` - The current status of the list (e.g., "active", "archived", "in_progress").
*   `created_at`: `DateTime` - Timestamp of when the list was created.
*   `updated_at`: `DateTime` - Timestamp of the last update.

**Relationships:**
*   **Many-to-One:** Many `ShoppingLists` belong to one `Household`.

---
#### Backend Model (Python/Pydantic)
```python
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from typing import List, Dict, Any, Optional

class ShoppingListItem(BaseModel):
    name: str
    quantity: float
    unit: str
    notes: Optional[str] = None

class ShoppingList(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    household_id: UUID
    name: str
    items: List[ShoppingListItem]
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True
```

#### Frontend Model (Dart)
```dart
import 'package:uuid/uuid.dart';

class ShoppingListItem {
  final String name;
  final double quantity;
  final String unit;
  final String? notes;

  ShoppingListItem({
    required this.name,
    required this.quantity,
    required this.unit,
    this.notes,
  });

  factory ShoppingListItem.fromJson(Map<String, dynamic> json) {
    return ShoppingListItem(
      name: json['name'],
      quantity: (json['quantity'] as num).toDouble(),
      unit: json['unit'],
      notes: json['notes'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'quantity': quantity,
      'unit': unit,
      'notes': notes,
    };
  }
}

class ShoppingList {
  final String id;
  final String householdId;
  final String name;
  final List<ShoppingListItem> items;
  final String status;
  final DateTime createdAt;
  final DateTime updatedAt;

  ShoppingList({
    required this.id,
    required this.householdId,
    required this.name,
    required this.items,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
  });

  factory ShoppingList.fromJson(Map<String, dynamic> json) {
    var itemsList = json['items'] as List;
    List<ShoppingListItem> items = itemsList.map((i) => ShoppingListItem.fromJson(i)).toList();

    return ShoppingList(
      id: json['id'],
      householdId: json['household_id'],
      name: json['name'],
      items: items,
      status: json['status'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'household_id': householdId,
      'name': name,
      'items': items.map((i) => i.toJson()).toList(),
      'status': status,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}
```
---

### 4.6. Order

**Purpose:** Represents a grocery order placed by a user through an integrated third-party service like Instacart. This model is essential for tracking the order's status, managing the affiliate revenue stream, and providing users with a history of their purchases.

**Key Attributes:**
*   `id`: `UUID` - The unique internal identifier for the order in our system.
*   `user_id`: `UUID` - The `id` of the user who placed the order.
*   `instacart_order_id`: `String` - The unique identifier for the order provided by the Instacart API. This is crucial for status lookups and support.
*   `status`: `String` - The current status of the order (e.g., "placed", "in_progress", "delivered", "cancelled"). This will be updated via webhooks or polling the Instacart API.
*   `created_at`: `DateTime` - Timestamp of when the order was placed in our system.
*   `updated_at`: `DateTime` - Timestamp of the last update to the order's status.

**Relationships:**
*   **Many-to-One:** Many `Orders` can be placed by one `User`.

---
#### Backend Model (Python/Pydantic)
```python
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime

class Order(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    instacart_order_id: str
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True
```

#### Frontend Model (Dart)
```dart
import 'package:uuid/uuid.dart';

class Order {
  final String id;
  final String userId;
  final String instacartOrderId;
  final String status;
  final DateTime createdAt;
  final DateTime updatedAt;

  Order({
    required this.id,
    required this.userId,
    required this.instacartOrderId,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Order.fromJson(Map<String, dynamic> json) {
    return Order(
      id: json['id'],
      userId: json['user_id'],
      instacartOrderId: json['instacart_order_id'],
      status: json['status'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'instacart_order_id': instacartOrderId,
      'status': status,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}
```
---

## 5. API Specification

### 5.1. REST API Specification (Partial)

```yaml
openapi: 3.0.0
info:
  title: "Bruno AI V3.1 API"
  version: "1.0.0"
  description: "API for the Bruno AI mobile application."
servers:
  - url: "/api"
    description: "Local development server"

paths:
  /users/register:
    post:
      summary: "Register a new user"
      tags:
        - "Authentication"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  format: password
                name:
                  type: string
      responses:
        "201":
          description: "User created successfully"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
        "400":
          description: "Invalid input or user already exists"

  /users/login:
    post:
      summary: "Log in a user"
      tags:
        - "Authentication"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  format: password
      responses:
        "200":
          description: "Login successful"
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                  token_type:
                    type: string
                    default: "bearer"
        "401":
          description: "Invalid credentials"

  /households:
    post:
      summary: "Create a new household"
      tags:
        - "Households"
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
      responses:
        "201":
          description: "Household created successfully"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Household"
        "401":
          description: "Unauthorized"

  /households/join:
    post:
      summary: "Join an existing household"
      tags:
        - "Households"
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                invite_code:
                  type: string
      responses:
        "200":
          description: "Successfully joined household"
          content:
            application/json:
              schema:
                type: object
                properties:
                  household_id:
                    type: string
                    format: uuid
        "404":
          description: "Household with that invite code not found"
        "401":
          description: "Unauthorized"

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        name:
          type: string
        household_id:
          type: string
          format: uuid
          nullable: true
    Household:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        admin_user_id:
          type: string
          format: uuid
        invite_code:
          type: string
```

---

## 6. Database Schema

### 6.1. SQL DDL (PostgreSQL)

```sql
-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table for Households
CREATE TABLE households (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    admin_user_id UUID NOT NULL, -- We will add the foreign key constraint after the users table is created
    invite_code VARCHAR(8) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create an index on the invite_code for fast lookups when a user tries to join
CREATE INDEX idx_households_invite_code ON households(invite_code);

-- Table for Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    voice_settings JSONB,
    dietary_preferences JSONB,
    household_id UUID, -- Nullable, as a user can exist without a household
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Foreign key constraint linking to the households table
    CONSTRAINT fk_household
        FOREIGN KEY(household_id) 
        REFERENCES households(id)
        ON DELETE SET NULL -- If a household is deleted, the user is not deleted, but their household link is removed
);

-- Create a unique index on email for fast login lookups
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- Now, add the foreign key constraint from households to users
ALTER TABLE households
ADD CONSTRAINT fk_admin_user
FOREIGN KEY (admin_user_id)
REFERENCES users(id)
ON DELETE RESTRICT; -- Prevent deleting a user who is the admin of a household

```

---

## 7. Frontend Component Plan

### 7.1. Screens (Top-Level Widgets)

1.  **`SplashScreen`**
    *   **Responsibility:** The initial screen shown when the app starts. It will check if a user is already logged in. If so, it navigates to `HomeScreen`; otherwise, it navigates to `LoginScreen`.

2.  **`LoginScreen`**
    *   **Responsibility:** Allows an existing user to log in using their email and password. Handles form validation and displays error messages. Provides a link to navigate to `RegistrationScreen`.

3.  **`RegistrationScreen`**
    *   **Responsibility:** Allows a new user to create an account by providing their name, email, and password. Handles form validation and displays errors.

4.  **`HouseholdPromptScreen`**
    *   **Responsibility:** Shown to new users after they register or to existing users who are not yet part of a household. It gives them two clear choices: "Create a Household" or "Join a Household".

5.  **`CreateHouseholdScreen`**
    *   **Responsibility:** A simple form with a single text field for the user to name their new household.

6.  **`JoinHouseholdScreen`**
    *   **Responsibility:** A form where the user can enter the `invite_code` to join an existing household.

7.  **`HomeScreen`**
    *   **Responsibility:** The main screen of the app, shown after a user is logged in and is part of a household. (This is the destination, not part of the auth flow itself).

### 7.2. Reusable Widgets (Building Blocks)

These widgets will be created once and used across multiple screens to ensure a consistent UI and reduce code duplication.

*   **`EmailInputField`**
    *   **Description:** A text field specifically for email input. Includes validation for a valid email format.
    *   **Used on:** `LoginScreen`, `RegistrationScreen`.

*   **`PasswordInputField`**
    *   **Description:** A text field for password input. Includes features like obscuring the text and an optional "show/hide" icon.
    - **Used on:** `LoginScreen`, `RegistrationScreen`.

*   **`PrimaryButton`**
    *   **Description:** A standard, styled button for form submission. It can show a loading indicator while an async operation (like an API call) is in progress.
    *   **Used on:** All form screens.

*   **`AuthFormContainer`**
    *   **Description:** A container widget that provides the standard layout for authentication screens, including the app logo, a title, and the form fields.
    *   **Used on:** `LoginScreen`, `RegistrationScreen`.

*   **`ErrorMessageWidget`**
    *   **Description:** A standardized widget to display error messages to the user (e.g., "Invalid credentials", "User already exists").
    *   **Used on:** `LoginScreen`, `RegistrationScreen`, `JoinHouseholdScreen`.

*   **`LoadingSpinner`**
    *   **Description:** A simple, centered loading indicator shown while data is being fetched or submitted.

---

## 8. Core Workflows

### 8.1. User Authentication & Household Setup Flow

```mermaid
sequenceDiagram
    participant User
    participant FlutterApp as Flutter App
    participant FastAPI as FastAPI Backend
    participant FirebaseAuth as Firebase Auth
    participant PostgreSQL as PostgreSQL DB

    alt New User Registration
        User->>FlutterApp: Enters Name, Email, Password & Clicks Register
        FlutterApp->>FastAPI: POST /users/register
        FastAPI->>FirebaseAuth: Create user with email/password
        FirebaseAuth-->>FastAPI: Returns success and Firebase UID
        FastAPI->>PostgreSQL: INSERT into users table (with Firebase UID)
        PostgreSQL-->>FastAPI: User record created
        FastAPI-->>FlutterApp: 201 Created (returns User object and JWT)
        FlutterApp->>User: Navigates to Household Prompt Screen
    else Existing User Login
        User->>FlutterApp: Enters Email, Password & Clicks Login
        FlutterApp->>FastAPI: POST /users/login
        FastAPI->>FirebaseAuth: Sign in with email/password
        FirebaseAuth-->>FastAPI: Returns success and ID Token
        FastAPI-->>FlutterApp: 200 OK (returns own access_token/JWT)
        FlutterApp->>User: Navigates to Home Screen
    end

    alt Create New Household
        User->>FlutterApp: Clicks "Create Household" & enters name
        FlutterApp->>FastAPI: POST /households (with JWT)
        FastAPI->>PostgreSQL: INSERT into households table
        PostgreSQL-->>FastAPI: Household record created
        FastAPI->>PostgreSQL: UPDATE user's household_id
        PostgreSQL-->>FastAPI: User record updated
        FastAPI-->>FlutterApp: 201 Created (returns Household object)
        FlutterApp->>User: Navigates to Home Screen
    else Join Existing Household
        User->>FlutterApp: Clicks "Join Household" & enters invite code
        FlutterApp->>FastAPI: POST /households/join (with JWT)
        FastAPI->>PostgreSQL: SELECT household by invite_code
        PostgreSQL-->>FastAPI: Returns household
        FastAPI->>PostgreSQL: UPDATE user's household_id
        PostgreSQL-->>FastAPI: User record updated
        FastAPI-->>FlutterApp: 200 OK
        FlutterApp->>User: Navigates to Home Screen
    end

```

---

## 9. Unified Project Structure

This monorepo structure is designed to support our full-stack application, separating deployable applications from shared code and configuration.

```plaintext
bruno-ai-v2/
├── apps/                       # Contains our deployable applications
│   ├── client/                 # The Flutter mobile application
│   │   ├── lib/
│   │   │   ├── main.dart
│   │   │   ├── core/           # Core services (API client, etc.)
│   │   │   ├── features/       # Feature-based modules (auth, pantry, etc.)
│   │   │   └── shared/         # Shared widgets and utilities
│   │   ├── pubspec.yaml
│   │   └── ...
│   └── server/                 # The Python FastAPI backend
│       ├── app/
│       │   ├── main.py
│       │   ├── api/            # API endpoint routers
│       │   ├── core/           # Core logic (config, security)
│       │   ├── crud/           # Repository pattern implementations
│       │   └── models/         # SQLAlchemy models
│       ├── poetry.lock
│       ├── pyproject.toml
│       └── ...
├── packages/                   # Shared code between apps
│   ├── shared-types/           # Shared TypeScript/Dart types (if needed)
│   └── eslint-config/          # Shared linting rules
├── infrastructure/             # Infrastructure as Code (Terraform)
│   ├── main.tf
│   └── variables.tf
├── docs/                       # Project documentation
│   ├── prd.md
│   └── architecture.md
├── .github/                    # CI/CD workflows
│   └── workflows/
│       └── ci.yaml
├── nx.json                     # Nx monorepo configuration
├── package.json                # Root package.json for scripts & tooling
└── README.md
```

---

## 10. Development Workflow

This section outlines the steps and commands required to set up and run the project locally.

### 10.1. Local Development Setup

**Prerequisites:**
Before starting, ensure you have the following installed:
*   Node.js and npm (for Nx and other tooling)
*   Flutter SDK
*   Python 3.11+ and Poetry
*   Docker Desktop
*   Terraform

**Initial Setup:**
These commands should be run once after cloning the repository.
```bash
# Install root-level dependencies (like Nx)
npm install

# Install Python dependencies for the server
cd apps/server
poetry install
cd ../..

# Install Dart dependencies for the client
cd apps/client
flutter pub get
cd ../..
```

**Development Commands:**
These commands are used for day-to-day development.
```bash
# Start the FastAPI backend server
nx serve server

# Run the Flutter client (launches the mobile simulator)
nx serve client

# Run all tests across the monorepo
nx run-many --target=test

# Run backend tests only
nx test server

# Run frontend tests only
nx test client
```

### 10.2. Environment Configuration

A `.env.example` file should be created at the root. Developers will copy this to a `.env` file for their local setup.

**Required Environment Variables (`.env`):**
```bash
# Backend (.env file in apps/server)
DATABASE_URL="postgresql://user:password@localhost:5432/bruno_ai"
SECRET_KEY="<generate_a_strong_random_string>" # For JWT signing
FIREBASE_PROJECT_ID="<your_firebase_project_id>"

# Frontend (not typically needed for local dev unless using --dart-define)
# API_BASE_URL="http://localhost:8000/api"
```

---

## 11. Deployment Architecture

This section details the strategy for deploying the frontend and backend applications to our chosen environments.

### 11.1. Deployment Strategy

**Frontend Deployment (Flutter App):**
*   **Platform:** Apple App Store & Google Play Store
*   **Build Command:** `flutter build appbundle` (for Android) and `flutter build ipa` (for iOS)
*   **Deployment Method:** The built application bundles will be uploaded to the respective app stores via their command-line tools or web consoles. This process will be automated using GitHub Actions.

**Backend Deployment (FastAPI Server):**
*   **Platform:** Google Cloud Run
*   **Build Command:** `docker build -t gcr.io/$PROJECT_ID/bruno-server:latest .`
*   **Deployment Method:** We will use a `Dockerfile` to containerize our FastAPI application. The Docker image will be pushed to Google Container Registry (GCR) and then deployed as a new revision to our Cloud Run service. This entire process will be automated via GitHub Actions.

### 11.2. CI/CD Pipeline (GitHub Actions)

Here is a high-level outline of our `ci.yaml` workflow file.

```yaml
# .github/workflows/ci.yaml
name: Bruno AI CI/CD

on:
  push:
    branches:
      - main # Deploy to production
      - staging # Deploy to staging

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js (for Nx)
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install Dependencies
        run: npm install
      - name: Run All Tests
        run: nx run-many --target=test

  deploy_backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      # ... steps to authenticate with GCP ...
      - name: Build and Push Docker Image
        run: |
          docker build -t gcr.io/$PROJECT_ID/bruno-server:latest ./apps/server
          docker push gcr.io/$PROJECT_ID/bruno-server:latest
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy bruno-server \
            --image gcr.io/$PROJECT_ID/bruno-server:latest \
            --platform managed \
            --region us-central1 \
            --allow-unauthenticated

  deploy_frontend:
    needs: test
    runs-on: macos-latest # Required for building iOS apps
    steps:
      # ... steps to authenticate with App Store Connect / Google Play ...
      - name: Build Flutter App
        run: |
          # Logic to build for either Android or iOS based on target
          flutter build appbundle
      - name: Deploy to App Store / Play Store
        run: |
          # Command to upload the bundle
```

### 11.3. Environments

| Environment | Frontend URL | Backend URL | Purpose |
| :--- | :--- | :--- | :--- |
| **Development** | Local Simulator | `http://localhost:8000` | Local development and testing |
| **Staging** | Internal Testing (TestFlight/Google Play Beta) | `https://staging-api.bruno.ai` | Pre-production testing, QA |
| **Production** | App Store / Play Store | `https://api.bruno.ai` | Live user environment |

---

## 12. Security and Performance

### 12.1. Security Requirements

**Frontend Security (Flutter):**
*   **Secure Storage:** All sensitive data, such as JWTs or API keys, will be stored on the device using the `flutter_secure_storage` package, which leverages the platform's native Keystore (Android) and Keychain (iOS).
*   **Network Security:** All API communication will be over HTTPS (TLS 1.3). We will implement SSL pinning to prevent man-in-the-middle attacks.
*   **Code Obfuscation:** The release builds of the Flutter app will be obfuscated to make it more difficult to reverse-engineer.

**Backend Security (FastAPI):**
*   **Input Validation:** All incoming data will be automatically validated by FastAPI using Pydantic models, preventing common injection attacks.
*   **Rate Limiting:** A rate limiter will be implemented as a middleware to protect against brute-force attacks and denial-of-service attempts.
*   **CORS Policy:** The Cross-Origin Resource Sharing (CORS) policy will be strictly configured to only allow requests from our authorized frontend domains (for potential future web versions).
*   **Dependency Scanning:** We will use a tool like `safety` or GitHub's Dependabot to automatically scan our Python dependencies for known vulnerabilities.

**Authentication Security:**
*   **Token Strategy:** We will use short-lived JWTs (JSON Web Tokens) for API authentication, with a refresh token mechanism to provide a seamless user experience.
*   **Password Policy:** All password complexity rules and secure storage are managed by Firebase Authentication, which is a secure, industry-standard service.

### 12.2. Performance Optimization

**Frontend Performance:**
*   **Loading Strategy:** The app will display loading indicators during network requests. We will use lazy loading for feature modules to keep the initial startup time fast.
*   **Caching Strategy:** API responses that don't change often will be cached locally on the device to reduce network requests and improve perceived performance.
*   **Build Optimization:** We will use Flutter's `--split-per-abi` flag to create smaller, more optimized Android app bundles.

**Backend Performance:**
*   **Response Time Target:** The target for all P95 API response times is **< 200ms** for non-AI-related queries.
*   **Database Optimization:** We will use the indexes defined in our schema and connection pooling (managed by SQLAlchemy) to ensure fast database queries.
*   **Asynchronous Operations:** For long-running tasks (like complex AI processing), we will use background workers to avoid blocking the main API thread and provide an immediate response to the user.
*   **Caching Strategy:** We will implement a Redis cache to store the results of expensive queries or frequently accessed data, reducing the load on our database.

---

## 13. Testing Strategy

### 13.1. Testing Pyramid

We will follow the standard testing pyramid model to guide our efforts, focusing on a large base of fast, isolated tests and a smaller number of slower, integrated tests.

```
                 /\
                /  \
               / E2E \   (Smallest, End-to-End Tests)
              /-------\
             /         \
            /   API   \  (Integration Tests)
           /           \
          /------------- \
         / Widget | Unit \ (Largest, Isolated Tests)
        /------------------\
```

### 13.2. Test Organization

*   **Frontend Tests (Flutter):**
    *   **Location:** `apps/client/test/`
    *   **Unit Tests:** For testing individual functions, classes, and BLoCs.
    *   **Widget Tests:** For testing individual Flutter widgets in isolation.
    *   **Integration Tests:** For testing complete features or user flows within the app.

*   **Backend Tests (FastAPI):**
    *   **Location:** `apps/server/tests/`
    *   **Unit Tests:** For testing individual functions, services, and utilities.
    *   **Integration Tests:** For testing the API endpoints, including their interaction with the database and other services.

### 13.3. Test Examples

**Frontend Widget Test Example (`apps/client/test/features/auth/login_screen_test.dart`):**
```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:bruno_app/features/auth/login_screen.dart'; // Fictional path

void main() {
  testWidgets('LoginScreen has a title, email field, and password field', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(MaterialApp(home: LoginScreen()));

    // Verify that our widgets are present.
    expect(find.text('Login'), findsOneWidget);
    expect(find.byType(TextFormField), findsNWidgets(2));
    expect(find.byType(ElevatedButton), findsOneWidget);
  });
}
```

**Backend Unit Test Example (`apps/server/tests/test_utils.py`):**
```python
from app.core.security import create_access_token
import jwt

def test_create_access_token():
    # Given
    data = {"sub": "test@example.com"}
    
    # When
    token = create_access_token(data)
    
    # Then
    decoded_data = jwt.decode(token, options={"verify_signature": False})
    assert decoded_data["sub"] == data["sub"]
```

**Backend Integration Test Example (`apps/server/tests/api/test_users.py`):**
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_user():
    # Given
    user_data = {
        "email": "test.user@example.com",
        "password": "a-strong-password",
        "name": "Test User"
    }

    # When
    response = client.post("/api/users/register", json=user_data)

    # Then
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "id" in data
```

---

## 14. Coding Standards

This section outlines the critical coding standards and naming conventions that all developers (human and AI) must follow. The goal is not to be exhaustive but to enforce a baseline of consistency.

### 14.1. Critical Fullstack Rules

*   **Type Sharing:** When a data type is used by both the frontend and backend, it must be defined in a shared package. Do not duplicate type definitions.
*   **API Calls:** The Flutter client must never make direct HTTP calls. All API interactions must be handled through a dedicated service layer (Repository Pattern) that abstracts the API client.
*   **Environment Variables:** Never access environment variables directly in the code (e.g., `process.env.VAR` or `os.getenv("VAR")`). Access them through a centralized configuration object to ensure consistency and make management easier.
*   **Error Handling:** All API endpoints must use the standard error handling middleware. Do not implement custom error responses in individual routes.
*   **State Updates:** In the Flutter app, never mutate state directly within a widget. All state changes must go through the defined state management solution (BLoC).
*   **No Hardcoded Strings:** All user-facing strings in the Flutter app must be managed in a centralized localization file, even for the initial English-only version. This makes future internationalization much easier.

### 14.2. Naming Conventions

| Element | Convention | Example |
| :--- | :--- | :--- |
| **Flutter Widgets** | `PascalCase` | `UserProfileCard.dart` |
| **Flutter BLoCs/Providers** | `PascalCase` | `AuthenticationBloc.dart` |
| **Python Files/Modules** | `snake_case` | `pantry_service.py` |
| **Python Classes** | `PascalCase` | `class PantryRepository:` |
| **API Endpoints** | `kebab-case` | `/api/pantry-items` |
| **Database Tables** | `snake_case` | `pantry_items` |
| **Database Columns** | `snake_case` | `expiration_date` |

---

## 15. Error Handling Strategy

This section defines the unified approach to error handling across both the frontend and backend.

### 15.1. Error Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant FlutterApp as Flutter App
    participant FastAPI as FastAPI Backend
    participant PostgreSQL as PostgreSQL DB

    FastAPI->>PostgreSQL: Executes a query that fails
    PostgreSQL-->>FastAPI: Returns a database error
    FastAPI->>FastAPI: Catches exception in middleware
    FastAPI->>FastAPI: Logs the full error details
    FastAPI-->>FlutterApp: Responds with a standardized JSON error (e.g., 500 Internal Server Error)

    FlutterApp->>FlutterApp: API client catches the HTTP error
    FlutterApp->>FlutterApp: Parses the standardized JSON error
    FlutterApp->>User: Displays a user-friendly error message (e.g., "Something went wrong. Please try again.")
```

### 15.2. Standardized Error Response Format

All errors returned from the API will follow this consistent JSON structure.

```typescript
interface ApiError {
  error: {
    code: string;       // e.g., "invalid_input", "unauthenticated", "internal_error"
    message: string;    // A developer-friendly error message
    details?: Record<string, any>; // Optional structured data, e.g., validation errors
    timestamp: string;  // ISO 8601 timestamp of the error
    requestId: string;  // A unique ID for tracing the request
  };
}
```

### 15.3. Backend Error Handling (FastAPI Middleware)

We will create a custom exception handler middleware in FastAPI to catch all exceptions and format them into our standard `ApiError` response.

```python
# app/core/error_handling.py (simplified example)
from fastapi import Request, status
from fastapi.responses import JSONResponse
import uuid

async def unified_exception_handler(request: Request, exc: Exception):
    request_id = str(uuid.uuid4())
    # In a real app, you would log the full exception `exc` here
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred.",
                "timestamp": datetime.utcnow().isoformat(),
                "requestId": request_id,
            }
        },
    )
```

### 15.4. Frontend Error Handling (API Client)

The API service layer in our Flutter app will be responsible for catching HTTP errors and parsing the `ApiError` response. The UI will then display a generic, user-friendly message while the full error details can be logged for debugging.

---

## 16. Monitoring and Observability

This section defines our strategy for monitoring the health, performance, and usage of the application.

### 16.1. Monitoring Stack

We will primarily leverage the integrated services provided by Google Cloud Platform, as they offer seamless integration with our chosen infrastructure.

*   **Frontend Monitoring:** **Firebase Performance Monitoring** and **Firebase Crashlytics**. These tools will automatically capture app startup time, screen render performance, and detailed crash reports from user devices.
*   **Backend Monitoring:** **Google Cloud's Operations Suite** (formerly Stackdriver). This includes:
    *   **Cloud Logging:** To aggregate logs from our FastAPI application running on Cloud Run.
    *   **Cloud Monitoring:** To track key metrics like CPU usage, memory, request latency, and error rates for our Cloud Run service and Cloud SQL database.
*   **Error Tracking:** We will use **Firebase Crashlytics** for the frontend and **Google Cloud Error Reporting** for the backend. Cloud Error Reporting automatically groups similar errors from our logs, making it easy to identify and prioritize new issues.

### 16.2. Key Metrics to Watch

**Frontend Metrics (via Firebase):**
*   **App Startup Time:** How long it takes for the app to be usable.
*   **Crash-Free Users:** The percentage of users who do not experience a crash. Target: > 99.5%.
*   **Screen Render Times:** To identify slow or janky UI.
*   **API Response Times (from client's perspective):** To measure the real-world latency users are experiencing.

**Backend Metrics (via Google Cloud Monitoring):**
*   **Request Rate:** The number of requests per second our API is handling.
*   **Error Rate:** The percentage of requests that result in a 5xx error. Target: < 0.1%.
*   **P95 Latency:** The 95th percentile response time for our API endpoints. Target: < 200ms.
*   **Database CPU & Memory Utilization:** To ensure our database is not overloaded.

---
