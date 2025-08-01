import 'package:mockito/annotations.dart';
import 'package:sqflite/sqflite.dart';

/// Mock definitions for database-related classes
/// 
/// This file defines the mock classes that will be generated by build_runner
/// for testing database functionality including:
/// - Database: SQLite database operations
/// - Batch: Batch database operations
/// - Transaction: Database transaction operations
@GenerateMocks([
  Database,
  Batch,
  Transaction,
])
void main() {}
