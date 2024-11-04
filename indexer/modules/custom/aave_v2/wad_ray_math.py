from decimal import Decimal
from typing import Union


class MathError:
    MATH_MULTIPLICATION_OVERFLOW = "Math: multiplication overflow"
    MATH_DIVISION_BY_ZERO = "Math: division by zero"
    MATH_ADDITION_OVERFLOW = "Math: addition overflow"


class WadRayMath:
    # Constants
    WAD: int = 10**18
    halfWAD: int = WAD // 2

    RAY: int = 10**27
    halfRAY: int = RAY // 2

    WAD_RAY_RATIO: int = 10**9

    MAX_UINT256: int = 2**256 - 1

    @classmethod
    def ray(cls) -> int:
        """Returns One ray, 1e27"""
        return cls.RAY

    @classmethod
    def wad(cls) -> int:
        """Returns One wad, 1e18"""
        return cls.WAD

    @classmethod
    def half_ray(cls) -> int:
        """Returns Half ray, 1e27/2"""
        return cls.halfRAY

    @classmethod
    def half_wad(cls) -> int:
        """Returns Half wad, 1e18/2"""
        return cls.halfWAD

    @classmethod
    def wad_mul(cls, a: int, b: int) -> int:
        """
        Multiplies two wad, rounding half up to the nearest wad
        Args:
            a: Wad
            b: Wad
        Returns:
            The result of a*b, in wad
        """
        if a == 0 or b == 0:
            return 0

        if a > (cls.MAX_UINT256 - cls.halfWAD) // b:
            raise ValueError(MathError.MATH_MULTIPLICATION_OVERFLOW)

        return (a * b + cls.halfWAD) // cls.WAD

    @classmethod
    def wad_div(cls, a: int, b: int) -> int:
        """
        Divides two wad, rounding half up to the nearest wad
        Args:
            a: Wad
            b: Wad
        Returns:
            The result of a/b, in wad
        """
        if b == 0:
            raise ValueError(MathError.MATH_DIVISION_BY_ZERO)

        half_b = b // 2
        if a > (cls.MAX_UINT256 - half_b) // cls.WAD:
            raise ValueError(MathError.MATH_MULTIPLICATION_OVERFLOW)

        return (a * cls.WAD + half_b) // b

    @classmethod
    def ray_mul(cls, a: int, b: int) -> int:
        """
        Multiplies two ray, rounding half up to the nearest ray
        Args:
            a: Ray
            b: Ray
        Returns:
            The result of a*b, in ray
        """
        if a == 0 or b == 0:
            return 0

        if a > (cls.MAX_UINT256 - cls.halfRAY) // b:
            raise ValueError(MathError.MATH_MULTIPLICATION_OVERFLOW)

        return (a * b + cls.halfRAY) // cls.RAY

    @classmethod
    def ray_div(cls, a: int, b: int) -> int:
        """
        Divides two ray, rounding half up to the nearest ray
        Args:
            a: Ray
            b: Ray
        Returns:
            The result of a/b, in ray
        """
        if b == 0:
            raise ValueError(MathError.MATH_DIVISION_BY_ZERO)

        half_b = b // 2
        if a > (cls.MAX_UINT256 - half_b) // cls.RAY:
            raise ValueError(MathError.MATH_MULTIPLICATION_OVERFLOW)

        return (a * cls.RAY + half_b) // b

    @classmethod
    def ray_to_wad(cls, a: int) -> int:
        """
        Casts ray down to wad
        Args:
            a: Ray
        Returns:
            a casted to wad, rounded half up to the nearest wad
        """
        half_ratio = cls.WAD_RAY_RATIO // 2
        result = half_ratio + a

        if result < half_ratio:
            raise ValueError(MathError.MATH_ADDITION_OVERFLOW)

        return result // cls.WAD_RAY_RATIO

    @classmethod
    def wad_to_ray(cls, a: int) -> int:
        """
        Converts wad up to ray
        Args:
            a: Wad
        Returns:
            a converted in ray
        """
        result = a * cls.WAD_RAY_RATIO

        if result // cls.WAD_RAY_RATIO != a:
            raise ValueError(MathError.MATH_MULTIPLICATION_OVERFLOW)

        return result


if __name__ == "__main__":
    a = WadRayMath.ray_div(833438411, 1001640979723543535807894066)
    b = WadRayMath.ray_div(2202000000, 1002440380256762149666684848)
    print(a, b, a + b)
