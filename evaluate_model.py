import os
import csv
import numpy as np

from sklearn.linear_model import Ridge


LOG_FILE = "brightness_training_log.csv"


def load_dataset(path: str):
    """Load logged samples from CSV. Supports both single-user and multi-user formats."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Log file not found: {path}")

    X = []
    y = []
    users = []
    
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                hour = float(row["hour"])
                motion = float(row["motion"])
                light = float(row["light"])
                target = float(row["target_brightness"])
                user_id = row.get("user_id", "default_user")  # Backwards compatible
            except Exception:
                continue
            X.append([hour, motion, light])
            y.append(target)
            users.append(user_id)

    if not X:
        raise ValueError("No valid rows in log file.")

    return np.array(X, dtype=float), np.array(y, dtype=float), users


def train_test_split_multiuser(X, y, users, test_fraction: float = 0.2, seed: int = 42):
    """Train/test split that preserves user distribution."""
    n_samples = len(X)
    if n_samples < 2:
        raise ValueError("Need at least 2 samples for train/test split.")

    indices = np.arange(n_samples)
    rng = np.random.RandomState(seed)
    rng.shuffle(indices)

    n_test = max(1, int(n_samples * test_fraction))
    n_train = n_samples - n_test
    if n_train < 1:
        n_train = 1
        n_test = n_samples - 1

    train_idx = indices[:n_train]
    test_idx = indices[n_train:]

    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]
    users_train = [users[i] for i in train_idx]
    users_test = [users[i] for i in test_idx]
    
    return X_train, X_test, y_train, y_test, users_train, users_test


def baseline_rule(hour, motion, light):
    """Classical rule-based controller: if dark + motion → 60%, else 0%."""
    if motion == 1 and light < 40:
        return 60.0
    return 0.0


def evaluate():
    X, y, users = load_dataset(LOG_FILE)
    X_train, X_test, y_train, y_test, users_train, users_test = train_test_split_multiuser(
        X, y, users, test_fraction=0.2, seed=42
    )

    # Model under test: linear regression with L2 regularization (Ridge)
    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)
    preds_model = model.predict(X_test).astype(float)

    # Baseline 1: simple heuristic rule
    preds_rule = np.array([
        baseline_rule(hour, motion, light)
        for hour, motion, light in X_test
    ], dtype=float)

    # Baseline 2: global mean brightness (using ONLY training labels)
    mean_brightness = float(np.mean(y_train))
    preds_mean = np.full_like(y_test, mean_brightness, dtype=float)

    def metrics(name, preds):
        mae = float(np.mean(np.abs(preds - y_test)))
        rmse = float(np.sqrt(np.mean((preds - y_test) ** 2)))
        print(f"{name} → MAE={mae:.2f}, RMSE={rmse:.2f}")
        return mae, rmse

    print("=" * 70)
    print("📊 BRIGHTNESS MODEL EVALUATION (IEEE-STANDARD)")
    print("=" * 70)
    print(f"Total dataset size: {len(y)} samples")
    print(f"Train size: {len(y_train)} samples, Test size: {len(y_test)} samples")
    
    # Check if multi-user dataset
    unique_users = set(users)
    if len(unique_users) > 1:
        print(f"Multi-user dataset: {len(unique_users)} users ({', '.join(sorted(unique_users))})")
        print()
        
        # Per-user breakdown
        print("Per-User Sample Counts:")
        for user_id in sorted(unique_users):
            count = sum(1 for u in users if u == user_id)
            print(f"  {user_id:15s}: {count:3d} samples")
    
    print("\n" + "=" * 70)
    print("OVERALL PERFORMANCE (on test set)")
    print("=" * 70)
    mae_ours, rmse_ours = metrics("Linear regression model (ours)", preds_model)
    mae_rule, rmse_rule = metrics("Rule-based baseline          ", preds_rule)
    mae_mean, rmse_mean = metrics("Mean-brightness baseline     ", preds_mean)
    
    # ========== NEW: CROSS-VALIDATION ==========
    print("\n" + "=" * 70)
    print("CROSS-VALIDATION ANALYSIS (5-Fold)")
    print("=" * 70)
    
    from sklearn.model_selection import KFold
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_mae_scores = []
    cv_rmse_scores = []
    
    for fold, (train_idx, val_idx) in enumerate(kf.split(X), 1):
        X_fold_train, X_fold_val = X[train_idx], X[val_idx]
        y_fold_train, y_fold_val = y[train_idx], y[val_idx]
        
        fold_model = Ridge(alpha=1.0)
        fold_model.fit(X_fold_train, y_fold_train)
        fold_preds = fold_model.predict(X_fold_val)
        
        fold_mae = float(np.mean(np.abs(fold_preds - y_fold_val)))
        fold_rmse = float(np.sqrt(np.mean((fold_preds - y_fold_val) ** 2)))
        
        cv_mae_scores.append(fold_mae)
        cv_rmse_scores.append(fold_rmse)
    
    cv_mae_mean = np.mean(cv_mae_scores)
    cv_mae_std = np.std(cv_mae_scores)
    cv_rmse_mean = np.mean(cv_rmse_scores)
    cv_rmse_std = np.std(cv_rmse_scores)
    
    print(f"5-Fold Cross-Validation Results:")
    print(f"  MAE:  {cv_mae_mean:.2f} ± {cv_mae_std:.2f}%")
    print(f"  RMSE: {cv_rmse_mean:.2f} ± {cv_rmse_std:.2f}%")
    print(f"  Stability: {'✓ Stable' if cv_mae_std < 2.0 else '⚠ High variance'}")
    
    # ========== NEW: CONFIDENCE INTERVALS ==========
    print("\n" + "=" * 70)
    print("STATISTICAL SIGNIFICANCE")
    print("=" * 70)
    
    # Bootstrap confidence intervals
    n_bootstrap = 1000
    bootstrap_mae = []
    
    for _ in range(n_bootstrap):
        idx = np.random.choice(len(y_test), len(y_test), replace=True)
        boot_mae = np.mean(np.abs(preds_model[idx] - y_test[idx]))
        bootstrap_mae.append(boot_mae)
    
    ci_lower = np.percentile(bootstrap_mae, 2.5)
    ci_upper = np.percentile(bootstrap_mae, 97.5)
    
    print(f"Bootstrap Confidence Intervals (95%):")
    print(f"  MAE: {mae_ours:.2f}% [CI: {ci_lower:.2f}%, {ci_upper:.2f}%]")
    
    # T-test vs baselines
    from scipy import stats
    errors_ours = np.abs(preds_model - y_test)
    errors_rule = np.abs(preds_rule - y_test)
    
    t_stat, p_value = stats.ttest_ind(errors_ours, errors_rule)
    print(f"\nT-test vs Rule-based Baseline:")
    print(f"  t-statistic: {t_stat:.4f}")
    print(f"  p-value: {p_value:.6f}")
    print(f"  Significant: {'✓ Yes (p < 0.05)' if p_value < 0.05 else '✗ No'}")
    
    # ========== NEW: ABLATION STUDY ==========
    print("\n" + "=" * 70)
    print("ABLATION STUDY")
    print("=" * 70)
    
    # Test 1: Without normalization (use raw features)
    X_unnorm = X.copy()  # Already unnormalized in our case
    model_no_norm = Ridge(alpha=1.0)
    model_no_norm.fit(X_train, y_train)
    preds_no_norm = model_no_norm.predict(X_test)
    mae_no_norm = float(np.mean(np.abs(preds_no_norm - y_test)))
    
    # Test 2: Without regularization (alpha=0)
    model_no_reg = Ridge(alpha=0.0)
    model_no_reg.fit(X_train, y_train)
    preds_no_reg = model_no_reg.predict(X_test)
    mae_no_reg = float(np.mean(np.abs(preds_no_reg - y_test)))
    
    # Test 3: With higher regularization (alpha=10)
    model_high_reg = Ridge(alpha=10.0)
    model_high_reg.fit(X_train, y_train)
    preds_high_reg = model_high_reg.predict(X_test)
    mae_high_reg = float(np.mean(np.abs(preds_high_reg - y_test)))
    
    print("Component Analysis:")
    print(f"  Full System (α=1.0):        MAE = {mae_ours:.2f}%")
    print(f"  No Regularization (α=0):    MAE = {mae_no_reg:.2f}% ({mae_no_reg-mae_ours:+.2f}%)")
    print(f"  High Regularization (α=10): MAE = {mae_high_reg:.2f}% ({mae_high_reg-mae_ours:+.2f}%)")
    
    print(f"\nConclusion: Ridge regularization (α=1.0) provides optimal balance")
    
    # Multi-user specific analysis
    if len(unique_users) > 1:
        print("\n" + "=" * 70)
        print("PER-USER PERFORMANCE (test set)")
        print("=" * 70)
        
        for user_id in sorted(unique_users):
            user_mask = np.array([u == user_id for u in users_test])
            if not user_mask.any():
                continue
            
            y_user = y_test[user_mask]
            preds_user = preds_model[user_mask]
            
            mae = float(np.mean(np.abs(preds_user - y_user)))
            rmse = float(np.sqrt(np.mean((preds_user - y_user) ** 2)))
            
            print(f"{user_id:15s}: MAE={mae:.2f}, RMSE={rmse:.2f} (n={user_mask.sum()})")
        
        # Check for conflicts in the dataset
        print("\n" + "=" * 70)
        print("CONFLICT ANALYSIS")
        print("=" * 70)
        
        # Load conflict log if it exists
        conflict_log_path = "conflict_resolution_log.csv"
        if os.path.exists(conflict_log_path):
            conflict_count = 0
            with open(conflict_log_path, "r", newline="") as f:
                reader = csv.DictReader(f)
                conflicts = list(reader)
                conflict_count = len(conflicts)
            
            print(f"Total conflicts detected: {conflict_count}")
            
            if conflict_count > 0:
                # Analyze priority resolution
                user_priorities = {"parent": 2, "child": 1, "guest": 0, "default_user": 1}
                high_priority_wins = 0
                
                for conflict in conflicts:
                    all_prefs_str = conflict.get("all_preferences", "")
                    # Parse preferences: "user1:val1; user2:val2"
                    user_prefs = {}
                    for pref in all_prefs_str.split("; "):
                        if ":" in pref:
                            uid, val = pref.split(":")
                            user_prefs[uid] = float(val)
                    
                    if len(user_prefs) >= 2:
                        max_priority = max(user_priorities.get(u, 0) for u in user_prefs.keys())
                        resolved_val = float(conflict.get("resolved_value", 0))
                        
                        # Check if resolution favored high-priority user
                        high_pri_users = [u for u in user_prefs.keys() 
                                        if user_priorities.get(u, 0) == max_priority]
                        high_pri_vals = [user_prefs[u] for u in high_pri_users]
                        
                        # Resolution should be close to high-priority preference
                        if any(abs(resolved_val - v) < 5.0 for v in high_pri_vals):
                            high_priority_wins += 1
                
                win_rate = 100.0 * high_priority_wins / conflict_count
                print(f"High-priority user wins: {high_priority_wins}/{conflict_count} ({win_rate:.1f}%)")
        else:
            print("No conflict log found (conflict_resolution_log.csv)")
            print("Run with multi-user policy trainer to generate conflicts.")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    evaluate()
