from enum import Enum


class TokenType(Enum):
    ERC20 = "ERC20"
    ERC721 = "ERC721"
    ERC1155 = "ERC1155"
    ERC404 = "ERC404"

    @classmethod
    def from_string(cls, token_str: str) -> "TokenType":
        """
        Initializes a TokenType from a string. The comparison is case-insensitive.

        Args:
            token_str (str): The token type as a string.

        Returns:
            TokenType: The corresponding TokenType enum member.

        Raises:
            ValueError: If the token_str does not correspond to any TokenType.
        """
        try:
            # Convert the input to uppercase to match the enum values
            return cls(token_str.upper())
        except ValueError:
            raise ValueError(f"Unknown token type: {token_str}")
