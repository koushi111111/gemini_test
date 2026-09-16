/// アプリ全体の実行時設定。
///
/// 値は `--dart-define` で上書きする。
/// 例: flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
class AppConfig {
  const AppConfig._();

  /// バックエンド(FastAPI)のベース URL。
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

  /// API のバージョンプレフィックス。
  static const String apiPrefix = '/api/v1';

  static Uri endpoint(String path) => Uri.parse('$apiBaseUrl$apiPrefix$path');
}
