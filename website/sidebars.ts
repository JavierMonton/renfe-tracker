import type { SidebarsConfig } from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    {
      type: 'doc',
      id: 'intro',
      label: 'Introduction',
    },
    {
      type: 'doc',
      id: 'installation',
      label: 'Installation',
    },
    {
      type: 'doc',
      id: 'configuration',
      label: 'Configuration',
    },
    {
      type: 'category',
      label: 'Features',
      collapsed: false,
      items: [
        'features/possible-trains',
        'features/price-range',
        'features/trip-tracking',
        'features/notifications',
      ],
    },
  ],
};

export default sidebars;
