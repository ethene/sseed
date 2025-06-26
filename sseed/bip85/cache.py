"""BIP85 caching optimization module.

Provides intelligent caching for BIP85 operations to optimize performance
when performing multiple derivations from the same master seed. This is
particularly useful for batch operations and GUI applications.

Phase 5: Optimization & Performance Tuning implementation.
"""

import hashlib
import time
from dataclasses import dataclass
from threading import RLock
from typing import (
    Any,
    Dict,
    Optional,
    cast,
)

from bip_utils import Bip32Secp256k1

from sseed.logging_config import get_logger

from .core import create_bip32_master_key

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Cache entry for BIP85 master keys and derived data."""

    value: Any
    created_at: float
    access_count: int = 0
    last_accessed: float = 0.0

    def __post_init__(self) -> None:
        """Initialize access tracking."""
        self.last_accessed = self.created_at


class Bip85Cache:
    """Thread-safe cache for BIP85 master keys and frequently accessed data."""

    def __init__(self, max_entries: int = 100, ttl_seconds: int = 3600):
        """Initialize BIP85 cache.

        Args:
            max_entries: Maximum number of cache entries to maintain
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = RLock()
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "cleanups": 0}

        logger.debug(
            "Initialized BIP85 cache: max_entries=%d, ttl=%ds", max_entries, ttl_seconds
        )

    def _generate_key(self, master_seed: bytes, prefix: str = "") -> str:
        """Generate cache key from master seed."""
        # Use SHA256 hash of master seed for cache key
        seed_hash = hashlib.sha256(master_seed).hexdigest()[:16]
        return f"{prefix}:{seed_hash}" if prefix else seed_hash

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        return (time.time() - entry.created_at) > self._ttl_seconds

    def _cleanup_expired(self) -> int:
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key
            for key, entry in self._cache.items()
            if (current_time - entry.created_at) > self._ttl_seconds
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            self._stats["cleanups"] += 1
            logger.debug("Cleaned up %d expired cache entries", len(expired_keys))

        return len(expired_keys)

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return

        # Find least recently used entry
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed)

        del self._cache[lru_key]
        self._stats["evictions"] += 1
        logger.debug("Evicted LRU cache entry: %s", lru_key[:16])

    def get_master_key(self, master_seed: bytes) -> Optional[Bip32Secp256k1]:
        """Get cached BIP32 master key or None if not cached."""
        with self._lock:
            key = self._generate_key(master_seed, "master_key")

            if key in self._cache:
                entry = self._cache[key]

                # Check if expired
                if self._is_expired(entry):
                    del self._cache[key]
                    self._stats["misses"] += 1
                    return None

                # Update access tracking
                entry.access_count += 1
                entry.last_accessed = time.time()
                self._stats["hits"] += 1

                logger.debug("Cache hit for master key: %s", key[:16])
                return entry.value

            self._stats["misses"] += 1
            return None

    def cache_master_key(self, master_seed: bytes, master_key: Bip32Secp256k1) -> None:
        """Cache BIP32 master key for future use."""
        with self._lock:
            # Cleanup expired entries
            self._cleanup_expired()

            # Evict entries if cache is at or will exceed capacity
            while len(self._cache) >= self._max_entries:
                self._evict_lru()

            key = self._generate_key(master_seed, "master_key")
            current_time = time.time()

            self._cache[key] = CacheEntry(
                value=master_key, created_at=current_time, last_accessed=current_time
            )

            logger.debug("Cached master key: %s", key[:16])

    def get_validation_result(
        self, application: int, length: int, index: int
    ) -> Optional[bool]:
        """Get cached validation result."""
        with self._lock:
            key = f"validation:{application}:{length}:{index}"

            if key in self._cache:
                entry = self._cache[key]

                if not self._is_expired(entry):
                    entry.access_count += 1
                    entry.last_accessed = time.time()
                    self._stats["hits"] += 1
                    return cast(bool, entry.value)
                else:
                    del self._cache[key]

            self._stats["misses"] += 1
            return None

    def cache_validation_result(
        self, application: int, length: int, index: int, is_valid: bool
    ) -> None:
        """Cache validation result."""
        with self._lock:
            # Only cache positive validation results (errors are cheap to re-validate)
            if not is_valid:
                return

            # Cleanup periodically
            if len(self._cache) % 50 == 0:
                self._cleanup_expired()

            # Evict entries if cache is at capacity
            while len(self._cache) >= self._max_entries:
                self._evict_lru()

            key = f"validation:{application}:{length}:{index}"
            current_time = time.time()

            self._cache[key] = CacheEntry(
                value=is_valid, created_at=current_time, last_accessed=current_time
            )

    def get_entropy_bytes_needed(self, application: int, length: int) -> Optional[int]:
        """Get cached entropy bytes calculation."""
        with self._lock:
            key = f"entropy_bytes:{application}:{length}"

            if key in self._cache:
                entry = self._cache[key]

                if not self._is_expired(entry):
                    entry.access_count += 1
                    entry.last_accessed = time.time()
                    self._stats["hits"] += 1
                    return cast(int, entry.value)
                else:
                    del self._cache[key]

            self._stats["misses"] += 1
            return None

    def cache_entropy_bytes_needed(
        self, application: int, length: int, bytes_needed: int
    ) -> None:
        """Cache entropy bytes calculation."""
        with self._lock:
            # Cleanup expired entries
            self._cleanup_expired()

            # Evict entries if cache is at capacity
            while len(self._cache) >= self._max_entries:
                self._evict_lru()

            key = f"entropy_bytes:{application}:{length}"
            current_time = time.time()

            self._cache[key] = CacheEntry(
                value=bytes_needed, created_at=current_time, last_accessed=current_time
            )

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            entry_count = len(self._cache)
            self._cache.clear()
            logger.debug("Cleared cache: %d entries removed", entry_count)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                (self._stats["hits"] / total_requests * 100)
                if total_requests > 0
                else 0
            )

            return {
                "cache_size": len(self._cache),
                "max_entries": self._max_entries,
                "ttl_seconds": self._ttl_seconds,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate_percent": round(hit_rate, 2),
                "evictions": self._stats["evictions"],
                "cleanups": self._stats["cleanups"],
                "total_requests": total_requests,
            }

    def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics including entry information."""
        with self._lock:
            stats = self.get_stats()

            # Add detailed entry statistics
            if self._cache:
                access_counts = [entry.access_count for entry in self._cache.values()]
                ages = [
                    time.time() - entry.created_at for entry in self._cache.values()
                ]

                stats.update(
                    {
                        "avg_access_count": sum(access_counts) / len(access_counts),
                        "max_access_count": max(access_counts),
                        "avg_age_seconds": sum(ages) / len(ages),
                        "oldest_entry_seconds": max(ages),
                    }
                )

            return stats


# Global cache instance
_global_cache: Optional[Bip85Cache] = None


def get_global_cache() -> Bip85Cache:
    """Get or create global BIP85 cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = Bip85Cache()
    return _global_cache


def clear_global_cache() -> None:
    """Clear global cache."""
    global _global_cache
    if _global_cache is not None:
        _global_cache.clear()
        _global_cache = None


def get_cache_stats() -> Dict[str, Any]:
    """Get global cache statistics."""
    return get_global_cache().get_stats()


class OptimizedBip32KeyManager:
    """Optimized BIP32 master key manager with caching."""

    def __init__(self, cache: Optional[Bip85Cache] = None):
        """Initialize with optional custom cache."""
        self._cache = cache or get_global_cache()

    def get_master_key(self, master_seed: bytes) -> Bip32Secp256k1:
        """Get BIP32 master key with caching optimization."""
        # Try cache first
        cached_key = self._cache.get_master_key(master_seed)
        if cached_key is not None:
            return cached_key

        # Create new master key
        master_key = create_bip32_master_key(master_seed)

        # Cache for future use
        self._cache.cache_master_key(master_seed, master_key)

        return master_key
