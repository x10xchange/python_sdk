class AccountModule(BaseModule):
    async def create_api_key(self, description: str, sign: Callable[[str], str]) -> str:
        request_path = "/api/v1/user/account/api-key"
        x = sign(request_path)

        # if description is None:
        #     description = "trading api key for account {}".format(account.id)
        #
        # signing_account: LocalAccount = Account.from_key(self.__l1_private_key())
        # time = datetime.now(timezone.utc)
        # auth_time_string = time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # l1_message = f"{request_path}@{auth_time_string}".encode(encoding="utf-8")
        # signable_message = encode_defunct(l1_message)
        # l1_signature = signing_account.sign_message(signable_message)
        # headers = {
        #     L1_AUTH_SIGNATURE_HEADER: l1_signature.signature.hex(),
        #     L1_MESSAGE_TIME_HEADER: auth_time_string,
        #     ACTIVE_ACCOUNT_HEADER: str(account.id),
        # }

        url = self._get_url(self._get_endpoint_config().onboarding_url, path=request_path)
        request = ApiKeyRequestModel(description=description)
        response = await send_post_request(
            await self.get_session(),
            url,
            ApiKeyResponseModel,
            json=request.to_api_request_json(),
            request_headers=headers,
        )
        response_data = response.data

        if response_data is None:
            raise ValidationError("No API key data returned from onboarding")

        return response_data.key
