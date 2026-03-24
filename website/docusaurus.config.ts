import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Renfe Tracker',
  tagline: 'Self-hosted Spanish train price tracker with alerts',
  favicon: 'img/favicon.ico',

  url: 'https://JavierMonton.github.io',
  baseUrl: '/renfe-tracker/',

  organizationName: 'JavierMonton',
  projectName: 'renfe-tracker',
  trailingSlash: false,

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'es', 'ca'],
    localeConfigs: {
      en: { label: 'English' },
      es: { label: 'Español' },
      ca: { label: 'Català' },
    },
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
          editUrl:
            'https://github.com/JavierMonton/renfe-tracker/tree/main/website/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/social-card.png',
    colorMode: {
      defaultMode: 'light',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Renfe Tracker',
      logo: {
        alt: 'Renfe Tracker Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          href: 'https://github.com/JavierMonton/renfe-tracker',
          label: 'GitHub',
          position: 'right',
        },
        {
          type: 'localeDropdown',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            { label: 'Getting Started', to: '/' },
            { label: 'Installation', to: '/installation' },
          ],
        },
        {
          title: 'Features',
          items: [
            { label: 'Possible Trains', to: '/features/possible-trains' },
            { label: 'Price Range', to: '/features/price-range' },
            { label: 'Trip Tracking', to: '/features/trip-tracking' },
            { label: 'Notifications', to: '/features/notifications' },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/JavierMonton/renfe-tracker',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Renfe Tracker. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'yaml', 'docker'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
