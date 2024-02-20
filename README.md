# IaC Examples Repository

Welcome to the Infrastructure as Code (IaC) Examples Repository! This open-source project aims to create a comprehensive collection of example configurations, templates, and scripts for cloud services across the major providers: AWS, Google Cloud, and Azure. Whether you're a cloud enthusiast, a developer, or an IT professional, your contributions can help others navigate the complexities of cloud infrastructure. Feel free to use whatever service, language or provider you see fit. From the AWS-CDK to Terraform we want to house examples of all.

## Contributing

We welcome contributions from the community! To submit your examples, please follow these steps:

1. **Fork the Repository:** Start by forking the repository to your own GitHub account.

2. **Add Your Example:** Place your example in the appropriate folder:

   - Name your folder after the service you are building (ex. `/eks-on-demand`)
   - AWS examples should go into the `aws/` directory.
   - Google Cloud examples should be placed in the `google-cloud/` directory.
   - Azure examples belong in the `azure/` directory.
   - Please make your directory house all necessary dependencies and scripts to run your code

   If your example spans multiple cloud providers, please place it in the `cross-cloud/` directory.

3. **Describe Your Example:** Ensure you include a README.md in your example's directory, explaining:
   - What your example does.
   - How to deploy it.
   - Any prerequisites or configurations needed.
4. **Create a Pull Request:** Once you've added your example and its README.md, create a pull request against our main branch. Please provide a brief description of your example and why it's a valuable addition.

## Guidelines

To maintain the quality and relevance of contributions, we ask that you adhere to the following guidelines:

- **No Duplication:** Before contributing, please check existing examples to avoid duplicates.
- **Security:** Do not include any personal credentials or sensitive information in your examples.
- **Licensing:** By submitting your examples, you agree that they will be distributed under the same license as this repository.

## Getting Help

If you have questions or need help with creating or submitting an example, please open an issue in this repository. Our community and maintainers are here to help!

If Discord is your medium join us here - [Discord](https://discord.gg/hcU4ZAkUss)

## License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.
