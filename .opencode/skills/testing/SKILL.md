---
name: testing
description: Use when writing and running tests. Covers unit tests, integration tests, end-to-end tests, mocking, and test-driven development.
---

# Testing Skill

## Instructions

Testing is the practice of verifying that software behaves as expected. A comprehensive testing strategy includes multiple levels of testing, from small unit tests to large end-to-end tests, each serving a different purpose. This skill covers test types, frameworks, mocking strategies, test-driven development, and testing best practices.

### The Test Pyramid

The test pyramid represents the ideal distribution of tests:

```
     ╱╲
    ╱ E2E ╲         Small number of end-to-end tests
   ╱────────╲
  ╱Integration╲     Medium number of integration tests
 ╱──────────────╲
╱  Unit Tests    ╲   Large number of unit tests (foundation)
╱──────────────────╲
```

**Unit Tests**: Test individual functions, methods, or classes in isolation. Fast, reliable, and easy to maintain. They should comprise ~70% of your test suite.

**Integration Tests**: Test interactions between components (database, API, file system). They verify that units work together correctly. ~20% of tests.

**End-to-End Tests**: Test the complete system from user interface to backend. They validate critical user journeys but are slow and brittle. ~10% of tests.

### Testing Terminology

| Term | Definition |
|------|------------|
| Assertion | A check that a condition is true |
| Mock | Replace real object with a fake that records calls |
| Stub | Provide canned answers to calls made during the test |
| Spy | Record information about how a function was called |
| Fixture | A fixed state used as a baseline for tests |
| Coverage | Metric of how much code is exercised by tests |
| TDD | Test-Driven Development (test first, code second) |
| BDD | Behavior-Driven Development (describe behavior in natural language) |

### Test Structure (AAA Pattern)

Every test should follow the Arrange-Act-Assert pattern:

```python
def test_user_registration():
    # Arrange: Set up test data and conditions
    email = "user@example.com"
    password = "SecurePass123!"

    # Act: Perform the action being tested
    user = register_user(email, password)

    # Assert: Verify the result
    assert user is not None
    assert user.email == email
    assert user.is_authenticated is True
```

## Examples

### Example 1: Unit Testing with pytest

```python
"""
Unit tests for a payment processing module.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Source code to test
class PaymentProcessor:
    def __init__(self, gateway, tax_calculator, notification_service):
        self.gateway = gateway
        self.tax_calculator = tax_calculator
        self.notification_service = notification_service

    def process_payment(self, order):
        if order.total <= 0:
            raise ValueError("Order total must be positive")

        tax = self.tax_calculator.calculate(order)
        total_with_tax = order.total + tax

        charge_result = self.gateway.charge(
            amount=total_with_tax,
            currency=order.currency,
            source=order.payment_source,
        )

        if charge_result.success:
            self.notification_service.send(
                recipient=order.customer_email,
                template='payment_confirmation',
                data={'order_id': order.id, 'amount': total_with_tax},
            )
            return PaymentResult(
                success=True,
                transaction_id=charge_result.transaction_id,
                amount=total_with_tax,
            )

        return PaymentResult(success=False, error=charge_result.error)


# Tests
class TestPaymentProcessor:
    @pytest.fixture
    def setup(self):
        gateway = Mock()
        tax_calculator = Mock()
        notification_service = Mock()
        processor = PaymentProcessor(gateway, tax_calculator, notification_service)
        return processor, gateway, tax_calculator, notification_service

    def test_successful_payment(self, setup):
        """Test that a valid payment is processed correctly."""
        # Arrange
        processor, gateway, tax_calculator, notification = setup
        order = Mock(total=Decimal('100.00'), currency='USD',
                     payment_source='tok_visa', customer_email='user@test.com',
                     id='ORD-001')

        tax_calculator.calculate.return_value = Decimal('10.00')
        gateway.charge.return_value = Mock(
            success=True, transaction_id='txn_123', error=None
        )

        # Act
        result = processor.process_payment(order)

        # Assert
        assert result.success is True
        assert result.transaction_id == 'txn_123'
        assert result.amount == Decimal('110.00')

        gateway.charge.assert_called_once_with(
            amount=Decimal('110.00'),
            currency='USD',
            source='tok_visa',
        )
        notification.send.assert_called_once()

    def test_payment_with_negative_total(self, setup):
        """Test that negative totals are rejected."""
        processor, gateway, tax_calculator, notification = setup
        order = Mock(total=Decimal('-50.00'))

        with pytest.raises(ValueError, match="Order total must be positive"):
            processor.process_payment(order)

        gateway.charge.assert_not_called()

    def test_failed_gateway_charge(self, setup):
        """Test handling of gateway failure."""
        processor, gateway, tax_calculator, notification = setup
        order = Mock(total=Decimal('100.00'), currency='USD',
                     payment_source='tok_decline')

        tax_calculator.calculate.return_value = Decimal('10.00')
        gateway.charge.return_value = Mock(
            success=False, transaction_id=None, error='Card declined'
        )

        result = processor.process_payment(order)

        assert result.success is False
        assert result.error == 'Card declined'
        notification.send.assert_not_called()

    @pytest.mark.parametrize("total,tax,expected_amount", [
        (Decimal('0.01'), Decimal('0'), Decimal('0.01')),
        (Decimal('100'), Decimal('20'), Decimal('120')),
        (Decimal('999.99'), Decimal('100'), Decimal('1099.99')),
    ])
    def test_various_amounts(self, setup, total, tax, expected_amount):
        """Test payment with various amount combinations."""
        processor, gateway, tax_calculator, notification = setup
        order = Mock(total=total, currency='USD', payment_source='tok_visa')

        tax_calculator.calculate.return_value = tax
        gateway.charge.return_value = Mock(success=True, transaction_id='txn_1')

        result = processor.process_payment(order)

        assert result.amount == expected_amount
```

### Example 2: Integration Tests with Database

```python
"""
Integration tests for database operations.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from your_app.models import Base, User, Order

# Fixture for test database
@pytest.fixture(scope='function')
def db_session():
    # Create in-memory SQLite database for testing
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


class TestUserRepository:
    def test_create_user(self, db_session):
        """Test user creation in database."""
        user = User(
            email='user@example.com',
            username='johndoe',
            password_hash='hashed_password',
        )
        db_session.add(user)
        db_session.commit()

        saved_user = db_session.query(User).filter_by(email='user@example.com').first()
        assert saved_user is not None
        assert saved_user.username == 'johndoe'
        assert saved_user.id is not None

    def test_unique_email_constraint(self, db_session):
        """Test that duplicate emails are rejected."""
        user1 = User(email='duplicate@example.com', username='user1')
        user2 = User(email='duplicate@example.com', username='user2')

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_user_orders_relationship(self, db_session):
        """Test user to orders relationship."""
        user = User(email='user@example.com', username='johndoe')
        order = Order(user=user, total=100.00)

        db_session.add(user)
        db_session.add(order)
        db_session.commit()

        # Reload from database
        saved_user = db_session.query(User).first()
        assert len(saved_user.orders) == 1
        assert saved_user.orders[0].total == 100.00

    def test_batch_user_creation(self, db_session):
        """Test creating multiple users."""
        users = [
            User(email=f'user{i}@example.com', username=f'user{i}')
            for i in range(10)
        ]
        db_session.add_all(users)
        db_session.commit()

        count = db_session.query(User).count()
        assert count == 10
```

### Example 3: API Testing with FastAPI/Flask

```python
"""
API endpoint tests using FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from your_app.main import app

client = TestClient(app)


class TestUserAPI:
    def test_register_user(self):
        """Test user registration endpoint."""
        response = client.post('/api/v1/users/register', json={
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'name': 'John Doe',
        })

        assert response.status_code == 201
        data = response.json()
        assert data['email'] == 'newuser@example.com'
        assert 'id' in data
        assert 'password' not in data  # Never return password

    def test_register_duplicate_email(self):
        """Test registration with existing email."""
        # First registration
        client.post('/api/v1/users/register', json={
            'email': 'duplicate@example.com',
            'password': 'Pass123!',
        })

        # Duplicate registration
        response = client.post('/api/v1/users/register', json={
            'email': 'duplicate@example.com',
            'password': 'Pass456!',
        })

        assert response.status_code == 409
        assert 'already exists' in response.json()['detail']

    def test_login_success(self):
        """Test successful login."""
        # Register user first
        client.post('/api/v1/users/register', json={
            'email': 'logintest@example.com',
            'password': 'TestPass123!',
        })

        # Login
        response = client.post('/api/v1/auth/login', json={
            'email': 'logintest@example.com',
            'password': 'TestPass123!',
        })

        assert response.status_code == 200
        assert 'access_token' in response.json()
        assert 'refresh_token' in response.json()

    def test_login_invalid_credentials(self):
        """Test login with wrong password."""
        response = client.post('/api/v1/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'WrongPass123!',
        })

        assert response.status_code == 401

    @pytest.mark.parametrize("payload,expected_status", [
        ({'email': 'invalid', 'password': 'test'}, 422),
        ({'email': '', 'password': 'test'}, 422),
        ({'email': 'test@test.com', 'password': '12'}, 422),
        ({}, 422),
    ])
    def test_validation(self, payload, expected_status):
        """Test input validation."""
        response = client.post('/api/v1/users/register', json=payload)
        assert response.status_code == expected_status
```

### Example 4: End-to-End Tests with Playwright

```typescript
/**
 * E2E tests for user registration flow.
 */

import { test, expect } from '@playwright/test';

test.describe('User Registration Flow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/register');
    });

    test('should display registration form', async ({ page }) => {
        await expect(page.locator('h1')).toHaveText('Create Account');
        await expect(page.locator('#email')).toBeVisible();
        await expect(page.locator('#password')).toBeVisible();
        await expect(page.locator('#confirm-password')).toBeVisible();
        await expect(page.locator('button[type="submit"]')).toHaveText('Sign Up');
    });

    test('should register user successfully', async ({ page }) => {
        const testEmail = `test-${Date.now()}@example.com`;

        await page.fill('#email', testEmail);
        await page.fill('#password', 'SecurePass123!');
        await page.fill('#confirm-password', 'SecurePass123!');
        await page.click('button[type="submit"]');

        // Wait for redirect to dashboard
        await page.waitForURL('/dashboard');
        await expect(page.locator('.welcome-message')).toContainText(testEmail);

        // Verify user can log out
        await page.click('#user-menu');
        await page.click('#logout');
        await page.waitForURL('/login');
    });

    test('should show validation errors', async ({ page }) => {
        // Submit with empty fields
        await page.click('button[type="submit"]');

        await expect(page.locator('.error-message'))
            .toContainText('Email is required');
        await expect(page.locator('.error-message'))
            .toContainText('Password is required');
    });

    test('should show password mismatch error', async ({ page }) => {
        await page.fill('#email', 'test@example.com');
        await page.fill('#password', 'Password1!');
        await page.fill('#confirm-password', 'DifferentPassword1!');
        await page.click('button[type="submit"]');

        await expect(page.locator('.error-message'))
            .toContainText('Passwords do not match');
    });

    test('should navigate to login page', async ({ page }) => {
        await page.click('text=Already have an account? Sign in');
        await page.waitForURL('/login');
        await expect(page.locator('h1')).toHaveText('Sign In');
    });
});
```

### Example 5: Mocking External Services

```python
"""
Mocking external API calls in tests.
"""

import pytest
import responses
import requests
from unittest.mock import patch, PropertyMock

# Source code that calls external API
class WeatherService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.weather.com/v1"

    def get_temperature(self, city: str) -> float:
        response = requests.get(
            f"{self.base_url}/current",
            params={'city': city, 'apikey': self.api_key},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        return data['current']['temp_c']

    def get_forecast(self, city: str, days: int) -> list:
        response = requests.get(
            f"{self.base_url}/forecast",
            params={'city': city, 'days': days, 'apikey': self.api_key},
            timeout=5,
        )
        response.raise_for_status()
        return response.json()['forecast']


# Tests with responses library
class TestWeatherService:
    @responses.activate
    def test_get_temperature_success(self):
        """Test successful temperature retrieval."""
        responses.add(
            responses.GET,
            "https://api.weather.com/v1/current",
            json={'current': {'temp_c': 22.5}},
            status=200,
        )

        service = WeatherService(api_key='test-key')
        temp = service.get_temperature('London')

        assert temp == 22.5

    @responses.activate
    def test_get_temperature_api_error(self):
        """Test API error handling."""
        responses.add(
            responses.GET,
            "https://api.weather.com/v1/current",
            json={'error': 'Rate limit exceeded'},
            status=429,
        )

        service = WeatherService(api_key='test-key')
        with pytest.raises(requests.exceptions.HTTPError):
            service.get_temperature('London')

    @responses.activate
    def test_get_temperature_timeout(self):
        """Test timeout handling."""
        responses.add(
            responses.GET,
            "https://api.weather.com/v1/current",
            body=requests.exceptions.Timeout(),
        )

        service = WeatherService(api_key='test-key')
        with pytest.raises(requests.exceptions.Timeout):
            service.get_temperature('London')

    @responses.activate
    def test_get_forecast(self):
        """Test forecast retrieval."""
        mock_forecast = [
            {'date': '2024-01-15', 'high': 20, 'low': 10},
            {'date': '2024-01-16', 'high': 22, 'low': 12},
        ]
        responses.add(
            responses.GET,
            "https://api.weather.com/v1/forecast",
            json={'forecast': mock_forecast},
            status=200,
        )

        service = WeatherService(api_key='test-key')
        forecast = service.get_forecast('Tokyo', 2)

        assert len(forecast) == 2
        assert forecast[0]['high'] == 20


# Tests with unittest.mock
class TestDatabaseService:
    @patch('your_app.database.get_connection')
    def test_user_creation(self, mock_get_conn):
        """Test user creation with mocked database."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        service = UserService()
        user = service.create_user('test@example.com', 'password')

        assert user is not None
        mock_cursor.execute.assert_called_once()

    @patch('your_app.analytics.track_event')
    @patch('your_app.email.send_welcome_email')
    def test_new_user_workflow(self, mock_send_email, mock_track):
        """Test full new user workflow with multiple mocks."""
        service = UserService()

        user = service.register_user('new@example.com', 'password')

        mock_send_email.assert_called_once_with(user.email)
        mock_track.assert_called_once_with('user_registered', user_id=user.id)
```

### Example 6: Property-Based Testing

```python
"""
Property-based testing with Hypothesis.
"""

from hypothesis import given, strategies as st, assume
from hypothesis.strategies import integers, text, lists, dictionaries
import pytest


# Functions to test
def sort_numbers(numbers: list) -> list:
    """Sort a list of numbers."""
    return sorted(numbers)


def validate_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def add_to_cart(cart: dict, item: str, quantity: int) -> dict:
    """Add an item to a shopping cart."""
    if quantity <= 0:
        raise ValueError("Quantity must be positive")

    updated_cart = dict(cart)
    if item in updated_cart:
        updated_cart[item] += quantity
    else:
        updated_cart[item] = quantity
    return updated_cart


# Property-based tests
class TestSortingProperties:
    @given(lists(integers()))
    def test_sorted_order(self, numbers):
        """Property: Result should be in non-decreasing order."""
        result = sort_numbers(numbers)
        for i in range(len(result) - 1):
            assert result[i] <= result[i + 1]

    @given(lists(integers()))
    def test_same_length(self, numbers):
        """Property: Result should have same length as input."""
        result = sort_numbers(numbers)
        assert len(result) == len(numbers)

    @given(lists(integers()))
    def test_same_elements(self, numbers):
        """Property: Result should contain same elements."""
        result = sort_numbers(numbers)
        assert sorted(result) == sorted(numbers)  # Same multiset

    @given(lists(integers()))
    def test_idempotent(self, numbers):
        """Property: Double sorting should not change result."""
        once = sort_numbers(numbers)
        twice = sort_numbers(once)
        assert once == twice


class TestEmailValidation:
    @given(text(min_size=1))
    def test_email_contains_at(self, email):
        """Property: Valid emails must contain exactly one @."""
        assume(validate_email(email))
        assert email.count('@') == 1

    @given(text(min_size=1))
    def test_username_before_at(self, email):
        """Property: Valid emails have non-empty username before @."""
        assume(validate_email(email))
        assert len(email.split('@')[0]) >= 1

    @given(text(min_size=1))
    def test_reversible(self, email):
        """Property: Email validation should be consistent."""
        result = validate_email(email)
        # If it returned True once, it should always return True
        assert result == validate_email(email)


class TestCartProperties:
    @given(dictionaries(keys=text(min_size=1), values=integers(min_value=1)),
           text(min_size=1), integers(min_value=1, max_value=100))
    def test_quantity_increases(self, cart, item, quantity):
        """Property: Adding items increases their quantity."""
        assume(item not in cart)  # New item
        result = add_to_cart(cart, item, quantity)
        assert result[item] == quantity
        for k, v in cart.items():
            assert result[k] == v

    @given(dictionaries(keys=text(min_size=1), values=integers(min_value=1)),
           text(min_size=1), integers(min_value=1, max_value=100))
    def test_commutative(self, cart, item, quantity):
        """Property: Adding same item twice is same as adding sum."""
        assume(item in cart)
        result = add_to_cart(cart, item, quantity)
        assert result[item] == cart[item] + quantity
```

### Example 7: Test Fixtures and Factories

```python
"""
Advanced test fixtures using factory_boy.
"""

import pytest
from factory import Factory, Faker, Sequence, SubFactory, post_generation
from datetime import datetime, timedelta
from your_app.models import User, Post, Comment, Category


# Factories
class UserFactory(Factory):
    class Meta:
        model = User

    id = Sequence(lambda n: n + 1)
    email = Faker('email')
    username = Faker('user_name')
    password_hash = Faker('sha256')
    is_active = True
    created_at = Faker('date_time_this_year')

    @post_generation
    def set_password(self, create, extracted, **kwargs):
        """Set password if provided."""
        if extracted:
            self.password = extracted


class CategoryFactory(Factory):
    class Meta:
        model = Category

    id = Sequence(lambda n: n + 1)
    name = Faker('word')
    slug = Faker('slug')


class PostFactory(Factory):
    class Meta:
        model = Post

    id = Sequence(lambda n: n + 1)
    title = Faker('sentence')
    content = Faker('paragraphs', nb=3)
    published = True
    author = SubFactory(UserFactory)
    category = SubFactory(CategoryFactory)
    created_at = Faker('date_time_this_month')
    updated_at = datetime.utcnow


class CommentFactory(Factory):
    class Meta:
        model = Comment

    id = Sequence(lambda n: n + 1)
    content = Faker('paragraph')
    author = SubFactory(UserFactory)
    post = SubFactory(PostFactory)
    created_at = Faker('date_time_this_week')


# Fixtures using factories
@pytest.fixture
def user(db):
    return UserFactory.create()

@pytest.fixture
def admin_user(db):
    return UserFactory.create(is_admin=True)

@pytest.fixture
def posts(db, user):
    return PostFactory.create_batch(5, author=user)

@pytest.fixture
def published_posts(db):
    return PostFactory.create_batch(3, published=True)

@pytest.fixture
def draft_posts(db):
    return PostFactory.create_batch(2, published=False)

@pytest.fixture
def post_with_comments(db):
    post = PostFactory.create()
    comments = CommentFactory.create_batch(3, post=post)
    return post, comments


# Usage in tests
class TestBlogAPI:
    def test_get_published_posts(self, client, published_posts):
        """Test retrieving published posts."""
        response = client.get('/api/posts/')
        assert response.status_code == 200
        data = response.json()
        assert len(data['results']) == len(published_posts)

    def test_get_post_with_comments(self, client, post_with_comments):
        """Test retrieving a post with its comments."""
        post, comments = post_with_comments
        response = client.get(f'/api/posts/{post.id}/')
        assert response.status_code == 200
        data = response.json()
        assert len(data['comments']) == len(comments)

    def test_create_post_as_admin(self, client, admin_user):
        """Test post creation by admin."""
        client.force_login(admin_user)
        response = client.post('/api/posts/', {
            'title': 'New Post',
            'content': 'Post content here',
        })
        assert response.status_code == 201
```

## Best Practices

### Test Design

- Write tests before code (TDD) for critical business logic
- Each test should verify one behavior only
- Use descriptive test names that explain the behavior being tested
- Follow the Arrange-Act-Assert pattern consistently
- Keep tests independent; no shared state between tests
- Use factories or builders for test data creation
- Avoid test interdependence; tests should run in any order

### Test Coverage

- Focus on covering business logic, not getters/setters
- Aim for 80%+ coverage on critical paths
- Use coverage tools to identify untested code, not as a gate
- Test edge cases: empty, null, boundary values, errors
- Include negative tests (testing that errors are handled correctly)

### Mocking Guidelines

- Mock external services (APIs, databases, file system)
- Do not mock things you do not own (unless unavoidable)
- Prefer dependency injection for testability
- Use realistic mock data that resembles production
- Verify mock interactions (call count, arguments)
- Avoid over-mocking; integration tests verify real interactions

### Test Maintenance

- Treat test code with the same quality standards as production code
- Refactor tests when they become brittle or hard to understand
- Remove or update tests when requirements change
- Run tests in CI for every commit
- Keep test suites fast; slow tests discourage running them
- Use test categorization (unit, integration, smoke) for targeted runs

## Common Mistakes

- **Testing implementation details**: Tests that break on refactoring without behavior changes are testing implementation, not behavior.
- **Flaky tests**: Tests that pass/fail intermittently erode trust. Fix flaky tests immediately or disable them.
- **100% coverage obsession**: Coverage is a metric, not a goal. Testing trivial getters/setters covers lines but not bugs.
- **Slow test suites**: Tests that take too long discourage developers from running them. Optimize slow tests.
- **Not testing error cases**: Happy-path testing misses most bugs. Always test error conditions and edge cases.
- **Shared mutable state**: Tests that depend on each other's data are fragile. Each test should set up its own state.
- **Over-mocking**: Mocking internal implementation details makes tests brittle. Mock at system boundaries only.
- **Large, unfocused tests**: Tests that verify too many things at once are hard to debug when they fail.
- **Ignoring test failures**: Red builds should be fixed immediately. A failing test suite loses its value.
- **Not running tests locally**: Developers should run relevant tests before pushing to avoid CI failures.

## Libraries

### Testing Frameworks

| Language | Framework | Description |
|----------|-----------|-------------|
| Python | pytest | Feature-rich testing framework |
| Python | unittest | Built-in standard library testing |
| JavaScript | Jest | Zero-config testing framework |
| JavaScript | Vitest | Vite-native, Jest-compatible |
| TypeScript | Playwright | E2E testing for all browsers |
| TypeScript | Cypress | E2E testing with time-travel |
| Java | JUnit 5 | Standard Java testing framework |
| Java | TestNG | Alternative testing framework |
| Go | testing | Built-in testing package |
| Go | testify | Assertions and mocking |
| Rust | cargo test | Built-in testing framework |
| Rust | proptest | Property-based testing |

### Mocking and Stubbing

| Library | Language | Purpose |
|---------|----------|---------|
| unittest.mock | Python | Built-in mocking |
| pytest-mock | Python | pytest integration for mock |
| Sinon.js | JavaScript | Spies, stubs, mocks |
| Mockito | Java | Mocking framework |
| testify/mock | Go | Mocking for Go interfaces |
| Mockall | Rust | Mocking for Rust traits |

## Design Principles

### Test Behavior, Not Implementation

Tests should verify what the code does, not how it does it. Implementation details change during refactoring; behavior should remain the same. Tests that break on refactoring are testing the wrong thing.

### Fast, Reliable, Isolated

Every test should be fast (milliseconds), reliable (same result every time), and independent (no shared state). A test suite that violates any of these principles will not serve its purpose.

### Write Tests for Confidence

The purpose of tests is to give confidence that the code works correctly. Write tests that cover the scenarios you are most worried about breaking. Not every line needs a test, but every critical behavior does.

### Test the Public API

Test through the public API of a module, not its internal functions. Internal functions are implementation details; testing them directly creates brittleness. If an internal function is complex enough to need direct testing, consider whether it should be a separate module.

## Coding Standards

### Test File Organization

```
tests/
  unit/
    test_payment_processor.py
    test_user_service.py
  integration/
    test_database.py
    test_api.py
  e2e/
    test_registration.py
    test_checkout.py
  conftest.py           # Shared fixtures
  factories.py           # Test data factories
```

### Test Naming

```python
# Test file: test_<module>.py
# Test class: Test<Component>
# Test function: test_<behavior>_<scenario>

def test_process_payment_success():
    """Test that valid payment is processed."""

def test_process_payment_insufficient_funds():
    """Test payment fails when funds are insufficient."""

def test_process_payment_invalid_card():
    """Test payment fails with expired card."""

def test_process_payment_rejects_negative_amount():
    """Test payment rejects negative amounts."""
```

### Assertion Style

```python
# Use specific assertions
assert result == expected_value
assert result is None
assert 'error message' in str(context.exception)

# Use pytest assertions (no need for self.assertEqual)
with pytest.raises(ValueError, match="Invalid input"):
    function_that_raises()

# Use truthiness checks
assert result.success
assert not result.errors
assert len(items) > 0
```
